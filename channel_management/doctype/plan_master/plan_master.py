import frappe
from frappe.model.document import Document


class PlanMaster(Document):

    def validate(self):
        self.validate_validity()

    def validate_validity(self):
        if self.validity_value <= 0:
            frappe.throw("Validity must be greater than 0.")

    def get_validity_in_days(self):
        """Return validity as number of days."""
        if self.validity_unit == "Days":
            return self.validity_value
        elif self.validity_unit == "Months":
            return self.validity_value * 30
        elif self.validity_unit == "Years":
            return self.validity_value * 365
        return self.validity_value
