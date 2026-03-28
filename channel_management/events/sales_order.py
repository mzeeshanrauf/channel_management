import frappe
from frappe.utils import add_days, add_months, add_years, today, getdate


# ─── Validate ─────────────────────────────────────────────────────────────────

def on_validate(doc, method=None):
    """
    For each Sales Order Item that has a plan linked:
     1. Fetch Channel Pricing (actual + discloseable)
     2. Set rate = actual_price, discloseable_rate = discloseable_price
     3. Compute price_gap and discloseable_amount
     4. Update header total_discloseable_amount
    """
    total_discloseable = 0.0
    partner = doc.get("channel_partner") or None

    for item in doc.items:
        plan_name = item.get("plan")
        if not plan_name:
            continue

        pricing = _get_channel_pricing(plan_name, partner)
        if not pricing:
            frappe.msgprint(
                f"No active Channel Pricing found for plan <b>{plan_name}</b>. "
                "Please set up pricing in Channel Pricing before proceeding.",
                indicator="orange",
                alert=True,
            )
            continue

        qty = item.qty or 1

        # Set actual rate (this becomes the real Sales Order rate)
        item.rate = pricing["actual_price"]
        item.amount = pricing["actual_price"] * qty

        # Set discloseable fields
        item.discloseable_rate = pricing["discloseable_price"]
        item.discloseable_amount = pricing["discloseable_price"] * qty
        item.price_gap = (pricing["actual_price"] - pricing["discloseable_price"]) * qty

        total_discloseable += item.discloseable_amount

    doc.total_discloseable_amount = total_discloseable


# ─── Submit ───────────────────────────────────────────────────────────────────

def on_submit(doc, method=None):
    """
    On Sales Order submit:
     - For each item with a plan, create a Customer Plan record.
    """
    for item in doc.items:
        plan_name = item.get("plan")
        if not plan_name:
            continue

        # Calculate end date from plan validity
        plan = frappe.get_doc("Plan Master", plan_name)
        start_date = getdate(doc.transaction_date or today())
        end_date = _calculate_end_date(start_date, plan)

        # Get first sales person from Sales Team
        sales_person = None
        if doc.sales_team:
            sales_person = doc.sales_team[0].sales_person

        # Avoid duplicates
        existing = frappe.db.get_value(
            "Customer Plan",
            {"sales_order": doc.name, "plan": plan_name},
            "name"
        )
        if existing:
            continue

        cp = frappe.new_doc("Customer Plan")
        cp.customer = doc.customer
        cp.plan = plan_name
        cp.sales_order = doc.name
        cp.sales_person = sales_person
        cp.start_date = start_date
        cp.end_date = end_date
        cp.status = "Active"
        cp.actual_rate_snapshot = item.rate or 0
        cp.discloseable_rate_snapshot = item.get("discloseable_rate") or 0
        cp.insert(ignore_permissions=True)

    frappe.msgprint(
        "Customer Plan(s) created successfully.",
        indicator="green",
        alert=True,
    )


# ─── Cancel ───────────────────────────────────────────────────────────────────

def on_cancel(doc, method=None):
    """Cancel related Customer Plans when Sales Order is cancelled."""
    plans = frappe.get_all(
        "Customer Plan",
        filters={"sales_order": doc.name, "status": ["!=", "Cancelled"]},
        fields=["name"]
    )
    for p in plans:
        cp = frappe.get_doc("Customer Plan", p.name)
        cp.status = "Cancelled"
        cp.save(ignore_permissions=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_channel_pricing(plan_name, partner=None):
    """
    Fetch the most applicable active Channel Pricing record.
    Prefers partner-specific pricing over generic pricing.
    """
    today_date = today()

    def _fetch(extra_filters):
        filters = {
            "plan": plan_name,
            "is_active": 1,
            "effective_date": ["<=", today_date],
        }
        filters.update(extra_filters)
        result = frappe.db.get_value(
            "Channel Pricing",
            filters,
            ["actual_price", "discloseable_price"],
            as_dict=True,
            order_by="effective_date desc",
        )
        return result

    # Try partner-specific first
    if partner:
        pricing = _fetch({"partner": partner})
        if pricing:
            return pricing

    # Fall back to generic (no partner)
    pricing = _fetch({"partner": ["is", "not set"]})
    return pricing


def _calculate_end_date(start_date, plan):
    """Compute end date from plan validity settings."""
    v = plan.validity_value
    unit = plan.validity_unit

    if unit == "Days":
        return add_days(start_date, v)
    elif unit == "Months":
        return add_months(start_date, v)
    elif unit == "Years":
        return add_years(start_date, v)
    return add_days(start_date, v)
