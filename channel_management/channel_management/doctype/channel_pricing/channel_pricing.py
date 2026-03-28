import frappe
from frappe.model.document import Document


class ChannelPricing(Document):

    def validate(self):
        self.validate_prices()
        self.calculate_gap()
        self.validate_dates()
        self.check_duplicate_active_pricing()

    def validate_prices(self):
        if self.actual_price <= 0:
            frappe.throw("Actual Price must be greater than 0.")
        if self.discloseable_price <= 0:
            frappe.throw("Discloseable Price must be greater than 0.")
        if self.discloseable_price > self.actual_price:
            frappe.throw(
                "Discloseable Price cannot be greater than Actual Price. "
                "Discloseable price is the reduced price shown to the sales team."
            )

    def calculate_gap(self):
        self.price_gap_display = self.actual_price - self.discloseable_price

    def validate_dates(self):
        if self.expiry_date and self.expiry_date < self.effective_date:
            frappe.throw("Expiry Date cannot be before Effective Date.")

    def check_duplicate_active_pricing(self):
        """Warn if another active pricing record exists for same plan+partner."""
        filters = {
            "plan": self.plan,
            "is_active": 1,
            "name": ["!=", self.name or ""],
        }
        if self.partner:
            filters["partner"] = self.partner
        else:
            filters["partner"] = ["is", "not set"]

        existing = frappe.db.get_value("Channel Pricing", filters, "name")
        if existing:
            frappe.msgprint(
                f"Warning: Another active pricing record exists for this plan "
                f"({existing}). Consider deactivating it.",
                indicator="orange",
                alert=True,
            )
