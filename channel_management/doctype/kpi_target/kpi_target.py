import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class KPITarget(Document):

    def validate(self):
        if self.period_end and self.period_start:
            if getdate(self.period_end) < getdate(self.period_start):
                frappe.throw("Period End cannot be before Period Start.")
        if self.target_value <= 0:
            frappe.throw("Target Value must be greater than 0.")
        self.set_period_label()
        self.calculate_achievement()

    def set_period_label(self):
        if not self.period_start:
            return
        d = getdate(self.period_start)
        if self.period_type == "Monthly":
            self.period_label = d.strftime("%b %Y")
        elif self.period_type == "Quarterly":
            q = (d.month - 1) // 3 + 1
            self.period_label = f"Q{q} {d.year}"
        else:
            self.period_label = str(d.year)

    def calculate_achievement(self):
        if not (self.sales_person and self.period_start and self.period_end):
            return

        self.achieved_value = get_achieved_value(
            self.sales_person, self.kpi_type,
            self.period_start, self.period_end
        )

        pct = (self.achieved_value / self.target_value * 100) if self.target_value else 0
        self.achievement_percentage = pct

        if pct >= 100:
            self.status = "Achieved"
        elif pct >= 70:
            self.status = "On Track"
        elif pct >= 40:
            self.status = "At Risk"
        else:
            self.status = "Missed"


def get_achieved_value(sales_person, kpi_type, period_start, period_end):
    """Calculate achieved value from approved Sales Forms."""

    if kpi_type == "Revenue":
        result = frappe.db.sql("""
            SELECT COALESCE(SUM(sf.total_sale_amount), 0)
            FROM `tabSales Form` sf
            WHERE sf.sales_person = %s
              AND sf.workflow_state = 'Approved'
              AND sf.transaction_date BETWEEN %s AND %s
        """, (sales_person, period_start, period_end))
        return result[0][0] if result else 0

    elif kpi_type == "Sales Count":
        result = frappe.db.sql("""
            SELECT COUNT(sf.name)
            FROM `tabSales Form` sf
            WHERE sf.sales_person = %s
              AND sf.workflow_state = 'Approved'
              AND sf.transaction_date BETWEEN %s AND %s
        """, (sales_person, period_start, period_end))
        return result[0][0] if result else 0

    elif kpi_type == "Renewals":
        result = frappe.db.sql("""
            SELECT COUNT(cp.name)
            FROM `tabCustomer Plan` cp
            JOIN `tabSales Form` sf ON sf.name = cp.sales_form
            WHERE cp.sales_person = %s
              AND cp.start_date BETWEEN %s AND %s
        """, (sales_person, period_start, period_end))
        return result[0][0] if result else 0

    return 0
