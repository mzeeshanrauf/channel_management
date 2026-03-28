import frappe
from frappe.model.document import Document
from frappe.utils import getdate, formatdate


class KPITarget(Document):

    def validate(self):
        self.validate_dates()
        self.set_period_label()
        self.calculate_achievement()

    def validate_dates(self):
        if self.period_end and self.period_start:
            if getdate(self.period_end) < getdate(self.period_start):
                frappe.throw("Period End cannot be before Period Start.")
        if self.target_value <= 0:
            frappe.throw("Target Value must be greater than 0.")

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
        """Calculate achieved value from submitted Sales Orders in period."""
        if not (self.sales_person and self.period_start and self.period_end):
            return

        self.achieved_value = _get_achieved_value(
            self.sales_person,
            self.kpi_type,
            self.period_start,
            self.period_end,
        )

        if self.target_value:
            self.achievement_percentage = (self.achieved_value / self.target_value) * 100
        else:
            self.achievement_percentage = 0

        pct = self.achievement_percentage
        if pct >= 100:
            self.status = "Achieved"
        elif pct >= 70:
            self.status = "On Track"
        elif pct >= 40:
            self.status = "At Risk"
        else:
            self.status = "Missed"


def _get_achieved_value(sales_person, kpi_type, period_start, period_end):
    """Fetch achieved value from Sales Orders for the given sales person and period."""

    so_filters = {
        "docstatus": 1,
        "transaction_date": ["between", [period_start, period_end]],
        "sales_team.sales_person": sales_person,
    }

    if kpi_type == "Revenue":
        # Sum of discloseable_amount from Sales Order Items
        result = frappe.db.sql("""
            SELECT COALESCE(SUM(soi.discloseable_amount), 0)
            FROM `tabSales Order` so
            JOIN `tabSales Team` st ON st.parent = so.name
            JOIN `tabSales Order Item` soi ON soi.parent = so.name
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND st.sales_person = %s
        """, (period_start, period_end, sales_person))
        return result[0][0] if result else 0

    elif kpi_type == "Sales Count":
        result = frappe.db.sql("""
            SELECT COUNT(DISTINCT so.name)
            FROM `tabSales Order` so
            JOIN `tabSales Team` st ON st.parent = so.name
            WHERE so.docstatus = 1
              AND so.transaction_date BETWEEN %s AND %s
              AND st.sales_person = %s
        """, (period_start, period_end, sales_person))
        return result[0][0] if result else 0

    elif kpi_type == "Renewals":
        result = frappe.db.sql("""
            SELECT COUNT(cp.name)
            FROM `tabCustomer Plan` cp
            JOIN `tabSales Order` so ON so.name = cp.sales_order
            JOIN `tabSales Team` st ON st.parent = so.name
            WHERE so.docstatus = 1
              AND cp.start_date BETWEEN %s AND %s
              AND st.sales_person = %s
        """, (period_start, period_end, sales_person))
        return result[0][0] if result else 0

    return 0
