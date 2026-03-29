import frappe
from frappe.model.document import Document
from frappe.utils import today


class SalesForm(Document):

    def validate(self):
        self.validate_sales_person()
        self.fetch_pricing_for_items()
        self.calculate_totals()

    def on_update_after_submit(self):
        pass

    def after_insert(self):
        pass

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_sales_person(self):
        if not self.sales_person:
            frappe.throw("Sales Person is required.")

    def fetch_pricing_for_items(self):
        """Fetch actual and sale amount from Channel Pricing for each plan row."""
        for row in self.plans:
            if not row.plan:
                continue

            pricing = get_channel_pricing(row.plan)
            if not pricing:
                frappe.msgprint(
                    f"No active Channel Pricing found for plan <b>{row.plan}</b>. "
                    "Please set up pricing before proceeding.",
                    indicator="orange",
                    alert=True,
                )
                continue

            row.sale_amount   = pricing["discloseable_price"]
            row.actual_amount = pricing["actual_price"]
            row.price_gap     = pricing["actual_price"] - pricing["discloseable_price"]

            # Validate dates
            if row.start_date and row.end_date:
                if row.end_date < row.start_date:
                    frappe.throw(
                        f"End Date cannot be before Start Date for plan {row.plan}."
                    )

    def calculate_totals(self):
        self.total_sale_amount   = sum(flt(r.sale_amount)   for r in self.plans)
        self.total_actual_amount = sum(flt(r.actual_amount) for r in self.plans)
        self.total_price_gap     = sum(flt(r.price_gap)     for r in self.plans)

    # ── Workflow hooks ────────────────────────────────────────────────────────

    def on_workflow_action(self, workflow_action):
        """Called when workflow action is taken."""
        if workflow_action == "Approve":
            self.create_customer_plans()

    def create_customer_plans(self):
        """Create Customer Plan records for each plan row when approved."""
        for row in self.plans:
            if not row.plan:
                continue

            existing = frappe.db.exists(
                "Customer Plan",
                {"sales_form": self.name, "plan": row.plan}
            )
            if existing:
                continue

            cp = frappe.new_doc("Customer Plan")
            cp.customer              = self.customer
            cp.plan                  = row.plan
            cp.sales_form            = self.name
            cp.sales_person          = self.sales_person
            cp.start_date            = row.start_date
            cp.end_date              = row.end_date
            cp.status                = "Active"
            cp.sale_amount_snapshot  = row.sale_amount
            cp.actual_amount_snapshot = row.actual_amount
            cp.insert(ignore_permissions=True)

        frappe.msgprint("Customer Plan(s) created.", indicator="green", alert=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_channel_pricing(plan, partner=None):
    """Fetch active Channel Pricing for a plan."""
    today_date = today()

    def _fetch(extra_filters):
        filters = {
            "plan": plan,
            "is_active": 1,
            "effective_date": ["<=", today_date],
        }
        filters.update(extra_filters)
        return frappe.db.get_value(
            "Channel Pricing",
            filters,
            ["actual_price", "discloseable_price"],
            as_dict=True,
            order_by="effective_date desc",
        )

    if partner:
        pricing = _fetch({"partner": partner})
        if pricing:
            return pricing

    return _fetch({"partner": ["is", "not set"]})


def flt(val):
    try:
        return float(val or 0)
    except Exception:
        return 0.0
