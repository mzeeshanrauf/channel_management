import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    validate_permissions()
    columns = get_columns()
    data    = get_data(filters)
    chart   = get_chart(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary


def validate_permissions():
    user = frappe.session.user
    if not (
        ("Channel Manager" in frappe.get_roles(user)) or
        ("Channel Sales" in frappe.get_roles(user)) or
        ("Administrator" in frappe.get_roles(user))
    ):
        frappe.throw(_("Not permitted."), frappe.PermissionError)


def get_columns():
    return [
        {"label": _("Sales Person"),  "fieldname": "sales_person",          "fieldtype": "Link",    "options": "Sales Person", "width": 160},
        {"label": _("Period"),        "fieldname": "period_label",           "fieldtype": "Data",    "width": 100},
        {"label": _("KPI Type"),      "fieldname": "kpi_type",               "fieldtype": "Data",    "width": 110},
        {"label": _("Target"),        "fieldname": "target_value",           "fieldtype": "Float",   "width": 120},
        {"label": _("Achieved"),      "fieldname": "achieved_value",         "fieldtype": "Float",   "width": 120},
        {"label": _("Achievement %"), "fieldname": "achievement_percentage", "fieldtype": "Percent", "width": 120},
        {"label": _("Status"),        "fieldname": "status",                 "fieldtype": "Data",    "width": 110},
        {"label": _("Period Start"),  "fieldname": "period_start",           "fieldtype": "Date",    "width": 110},
        {"label": _("Period End"),    "fieldname": "period_end",             "fieldtype": "Date",    "width": 110},
    ]


def get_data(filters):
    user       = frappe.session.user
    is_manager = ("Channel Manager" in frappe.get_roles(user)) or ("Administrator" in frappe.get_roles(user))

    conditions = []
    values     = {}

    if not is_manager:
        from channel_management.utils import get_sales_person_for_user
        sp = get_sales_person_for_user(user)
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

    if filters.get("from_date"):
        conditions.append("kt.period_start >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("kt.period_end <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    data = frappe.db.sql(f"""
        SELECT kt.sales_person, kt.period_label, kt.kpi_type,
               kt.target_value, kt.achieved_value,
               kt.achievement_percentage, kt.status,
               kt.period_start, kt.period_end
        FROM `tabKPI Target` kt
        {where}
        ORDER BY kt.period_start DESC, kt.sales_person ASC
    """, values, as_dict=True)

    status_map = {
        "Achieved": "<span style='color:green;font-weight:bold'>✅ Achieved</span>",
        "On Track": "<span style='color:#2196F3;font-weight:bold'>🔵 On Track</span>",
        "At Risk":  "<span style='color:orange;font-weight:bold'>⚠️ At Risk</span>",
        "Missed":   "<span style='color:red;font-weight:bold'>❌ Missed</span>",
    }
    for row in data:
        row["status"] = status_map.get(row.status, row.status)

    return data


def get_chart(data):
    if not data:
        return None
    labels   = [f"{r.get('sales_person','')} ({r.get('period_label','')})" for r in data]
    targets  = [r.get("target_value", 0)   for r in data]
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
    }


def get_summary(data):
    if not data:
        return []
    achieved = sum(1 for r in data if "Achieved" in str(r.get("status", "")))
    on_track = sum(1 for r in data if "On Track" in str(r.get("status", "")))
    at_risk  = sum(1 for r in data if "At Risk"  in str(r.get("status", "")))
    missed   = sum(1 for r in data if "Missed"   in str(r.get("status", "")))
    return [
        {"label": _("Achieved"), "value": achieved, "datatype": "Int", "indicator": "green"},
        {"label": _("On Track"), "value": on_track, "datatype": "Int", "indicator": "blue"},
        {"label": _("At Risk"),  "value": at_risk,  "datatype": "Int", "indicator": "orange"},
        {"label": _("Missed"),   "value": missed,   "datatype": "Int", "indicator": "red"},
    ]
