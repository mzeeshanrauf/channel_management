import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    validate_permissions()
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def validate_permissions():
    user = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user)
    is_sales   = frappe.has_role("Channel Sales", user=user)
    if not (is_manager or is_sales or frappe.has_role("Administrator", user=user)):
        frappe.throw(_("You do not have permission to view this report."), frappe.PermissionError)


def get_columns(filters):
    cols = [
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Link",
         "options": "Sales Person", "width": 160},
        {"label": _("Period"),       "fieldname": "period_label",  "fieldtype": "Data",  "width": 100},
        {"label": _("KPI Type"),     "fieldname": "kpi_type",      "fieldtype": "Data",  "width": 110},
        {"label": _("Target"),       "fieldname": "target_value",  "fieldtype": "Float", "width": 120},
        {"label": _("Achieved"),     "fieldname": "achieved_value","fieldtype": "Float", "width": 120},
        {"label": _("Achievement %"),"fieldname": "achievement_percentage","fieldtype": "Percent","width": 120},
        {"label": _("Status"),       "fieldname": "status",        "fieldtype": "Data",  "width": 100},
        {"label": _("Period Start"), "fieldname": "period_start",  "fieldtype": "Date",  "width": 110},
        {"label": _("Period End"),   "fieldname": "period_end",    "fieldtype": "Date",  "width": 110},
    ]
    return cols


def get_data(filters):
    user       = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user)
    is_admin   = frappe.has_role("Administrator", user=user)

    conditions = []
    values     = {}

    # Sales team sees only their own KPIs
    if not (is_manager or is_admin):
        sp = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if not sp:
            return []
        conditions.append("kt.sales_person = %(sales_person)s")
        values["sales_person"] = sp
    elif filters.get("sales_person"):
        conditions.append("kt.sales_person = %(sales_person)s")
        values["sales_person"] = filters["sales_person"]

    if filters.get("kpi_type"):
        conditions.append("kt.kpi_type = %(kpi_type)s")
        values["kpi_type"] = filters["kpi_type"]

    if filters.get("period_type"):
        conditions.append("kt.period_type = %(period_type)s")
        values["period_type"] = filters["period_type"]

    if filters.get("from_date"):
        conditions.append("kt.period_start >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("kt.period_end <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    data = frappe.db.sql(f"""
        SELECT
            kt.sales_person,
            kt.period_label,
            kt.kpi_type,
            kt.target_value,
            kt.achieved_value,
            kt.achievement_percentage,
            kt.status,
            kt.period_start,
            kt.period_end
        FROM `tabKPI Target` kt
        {where}
        ORDER BY kt.period_start DESC, kt.sales_person ASC
    """, values, as_dict=True)

    # Color-code status
    for row in data:
        if row.status == "Achieved":
            row["status"] = f"<span style='color:green;font-weight:bold'>✅ Achieved</span>"
        elif row.status == "On Track":
            row["status"] = f"<span style='color:#2196F3;font-weight:bold'>🔵 On Track</span>"
        elif row.status == "At Risk":
            row["status"] = f"<span style='color:orange;font-weight:bold'>⚠️ At Risk</span>"
        elif row.status == "Missed":
            row["status"] = f"<span style='color:red;font-weight:bold'>❌ Missed</span>"

    return data


def get_chart(data):
    if not data:
        return None

    labels   = [f"{r.get('sales_person','')} ({r.get('period_label','')})" for r in data]
    targets  = [r.get("target_value", 0) for r in data]
    achieved = [r.get("achieved_value", 0) for r in data]

    return {
        "data": {
            "labels": labels[:15],
            "datasets": [
                {"name": "Target",   "values": targets[:15]},
                {"name": "Achieved", "values": achieved[:15]},
            ]
        },
        "type": "bar",
        "colors": ["#7575ff", "#00bfa5"],
        "barOptions": {"stacked": 0},
    }
