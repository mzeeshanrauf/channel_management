import frappe
from frappe.model.document import Document


class ChannelPricing(Document):

    def validate(self):
        if self.actual_price <= 0:
            frappe.throw("Actual Price must be greater than 0.")
        if self.discloseable_price <= 0:
            frappe.throw("Sale Amount must be greater than 0.")
        if self.discloseable_price > self.actual_price:
            frappe.throw("Sale Amount cannot be greater than Actual Price.")
        if self.expiry_date and self.expiry_date < self.effective_date:
            frappe.throw("Expiry Date cannot be before Effective Date.")
        self.price_gap = self.actual_price - self.discloseable_price
