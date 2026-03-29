import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff, getdate


class CustomerPlan(Document):

    def validate(self):
        if self.end_date and self.start_date:
            if getdate(self.end_date) < getdate(self.start_date):
                frappe.throw("End Date cannot be before Start Date.")
        self.calculate_days_to_expiry()
        self.set_status()

    def calculate_days_to_expiry(self):
        if self.end_date:
            self.days_to_expiry = date_diff(self.end_date, today())

    def set_status(self):
        if self.status == "Cancelled":
            return
        if not self.end_date:
            self.status = "Active"
            return

        days_left = date_diff(self.end_date, today())
        self.days_to_expiry = days_left

        if days_left < 0:
            self.status = "Expired"
        elif days_left <= 7:
            self.status = "Renewal Required"
        elif days_left <= 30:
            self.status = "Expiring Soon"
        else:
            self.status = "Active"
