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
        frappe.has_role("Channel Manager", user=user) or
        frappe.has_role("Administrator",   user=user)
    ):
        frappe.throw(_("Sales Margin Report is for Channel Managers only."), frappe.PermissionError)


def get_columns():
    return [
        {"label": _("Sales Form"),      "fieldname": "sales_form",      "fieldtype": "Link",     "options": "Sales Form", "width": 140},
        {"label": _("Date"),            "fieldname": "transaction_date","fieldtype": "Date",     "width": 100},
        {"label": _("Customer"),        "fieldname": "customer",        "fieldtype": "Link",     "options": "Customer",   "width": 160},
        {"label": _("Sales Person"),    "fieldname": "sales_person",    "fieldtype": "Link",     "options": "Sales Person","width": 140},
        {"label": _("Plan"),            "fieldname": "plan",            "fieldtype": "Link",     "options": "Plan Master", "width": 140},
        {"label": _("Start Date"),      "fieldname": "start_date",      "fieldtype": "Date",     "width": 100},
        {"label": _("End Date"),        "fieldname": "end_date",        "fieldtype": "Date",     "width": 100},
        {"label": _("Sale Amount"),     "fieldname": "sale_amount",     "fieldtype": "Currency", "width": 130},
        {"label": _("Actual Amount"),   "fieldname": "actual_amount",   "fieldtype": "Currency", "width": 130},
        {"label": _("Price Gap"),       "fieldname": "price_gap",       "fieldtype": "Currency", "width": 120},
        {"label": _("Margin %"),        "fieldname": "margin_pct",      "fieldtype": "Percent",  "width": 100},
        {"label": _("Status"),          "fieldname": "status",          "fieldtype": "Data",     "width": 130},
    ]


def get_data(filters):
    conditions = ["sf.workflow_state = 'Approved'"]
    values     = {}

    if filters.get("from_date"):
        conditions.append("sf.transaction_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("sf.transaction_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("customer"):
        conditions.append("sf.customer = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("sales_person"):
        conditions.append("sf.sales_person = %(sales_person)s")
        values["sales_person"] = filters["sales_person"]

    if filters.get("plan"):
        conditions.append("sfi.plan = %(plan)s")
        values["plan"] = filters["plan"]

    where = "WHERE " + " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            sf.name                AS sales_form,
            sf.transaction_date,
            sf.customer,
            sf.sales_person,
            sfi.plan,
            sfi.start_date,
            sfi.end_date,
            sfi.sale_amount,
            sfi.actual_amount,
            sfi.price_gap,
            sf.workflow_state      AS status
        FROM `tabSales Form` sf
        JOIN `tabSales Form Item` sfi ON sfi.parent = sf.name
        {where}
        ORDER BY sf.transaction_date DESC
    """, values, as_dict=True)

    for row in data:
        if row.actual_amount and row.actual_amount != 0:
            row["margin_pct"] = (row.price_gap / row.actual_amount) * 100
        else:
            row["margin_pct"] = 0

    return data


def get_chart(data):
    if not data:
        return None
    sp_map = {}
    for row in data:
        sp = row.sales_person or "Unknown"
        if sp not in sp_map:
            sp_map[sp] = {"sale": 0, "actual": 0, "gap": 0}
        sp_map[sp]["sale"]   += row.sale_amount   or 0
        sp_map[sp]["actual"] += row.actual_amount or 0
        sp_map[sp]["gap"]    += row.price_gap     or 0

    labels = list(sp_map.keys())[:15]
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Sale Amount",   "values": [sp_map[l]["sale"]   for l in labels]},
                {"name": "Actual Amount", "values": [sp_map[l]["actual"] for l in labels]},
                {"name": "Price Gap",     "values": [sp_map[l]["gap"]    for l in labels]},
            ]
        },
        "type": "bar",
        "colors": ["#00bfa5", "#5e64ff", "#ff5858"],
    }


def get_summary(data):
    if not data:
        return []
    total_sale   = sum(r.sale_amount   or 0 for r in data)
    total_actual = sum(r.actual_amount or 0 for r in data)
    total_gap    = sum(r.price_gap     or 0 for r in data)
    avg_margin   = (total_gap / total_actual * 100) if total_actual else 0
    return [
        {"label": _("Total Sale Amount"),   "value": total_sale,         "datatype": "Currency", "indicator": "green"},
        {"label": _("Total Actual Amount"), "value": total_actual,       "datatype": "Currency", "indicator": "blue"},
        {"label": _("Total Price Gap"),     "value": total_gap,          "datatype": "Currency", "indicator": "orange"},
        {"label": _("Average Margin %"),    "value": round(avg_margin,2),"datatype": "Percent",  "indicator": "purple"},
    ]
