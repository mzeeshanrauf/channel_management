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
    if not (frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user)):
        frappe.throw(
            _("Sales Margin Report is restricted to Channel Managers only."),
            frappe.PermissionError
        )


def get_columns():
    return [
        {"label": _("Sales Order"),         "fieldname": "sales_order",          "fieldtype": "Link",     "options": "Sales Order", "width": 150},
        {"label": _("Date"),                "fieldname": "transaction_date",     "fieldtype": "Date",     "width": 100},
        {"label": _("Customer"),            "fieldname": "customer",             "fieldtype": "Link",     "options": "Customer",    "width": 150},
        {"label": _("Sales Person"),        "fieldname": "sales_person",         "fieldtype": "Data",     "width": 140},
        {"label": _("Plan"),                "fieldname": "plan",                 "fieldtype": "Link",     "options": "Plan Master", "width": 140},
        {"label": _("Item"),                "fieldname": "item_code",            "fieldtype": "Link",     "options": "Item",        "width": 130},
        {"label": _("Qty"),                 "fieldname": "qty",                  "fieldtype": "Float",    "width": 70},
        {"label": _("Actual Rate"),         "fieldname": "actual_rate",          "fieldtype": "Currency", "width": 120},
        {"label": _("Actual Amount"),       "fieldname": "actual_amount",        "fieldtype": "Currency", "width": 130},
        {"label": _("Discloseable Rate"),   "fieldname": "discloseable_rate",    "fieldtype": "Currency", "width": 140},
        {"label": _("Discloseable Amount"), "fieldname": "discloseable_amount",  "fieldtype": "Currency", "width": 150},
        {"label": _("Price Gap (Item)"),    "fieldname": "price_gap",            "fieldtype": "Currency", "width": 130},
        {"label": _("Margin %"),            "fieldname": "margin_pct",           "fieldtype": "Percent",  "width": 100},
    ]


def get_data(filters):
    conditions = ["so.docstatus = 1"]
    values     = {}

    if filters.get("from_date"):
        conditions.append("so.transaction_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("so.transaction_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("customer"):
        conditions.append("so.customer = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("sales_person"):
        conditions.append("st.sales_person = %(sales_person)s")
        values["sales_person"] = filters["sales_person"]

    if filters.get("plan"):
        conditions.append("soi.plan = %(plan)s")
        values["plan"] = filters["plan"]

    where = " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            so.name                          AS sales_order,
            so.transaction_date,
            so.customer,
            GROUP_CONCAT(DISTINCT st.sales_person SEPARATOR ', ') AS sales_person,
            soi.plan,
            soi.item_code,
            soi.qty,
            soi.rate                         AS actual_rate,
            soi.amount                       AS actual_amount,
            COALESCE(soi.discloseable_rate, 0)   AS discloseable_rate,
            COALESCE(soi.discloseable_amount, 0) AS discloseable_amount,
            COALESCE(soi.price_gap, 0)           AS price_gap
        FROM `tabSales Order` so
        JOIN `tabSales Order Item` soi ON soi.parent = so.name
        LEFT JOIN `tabSales Team` st ON st.parent = so.name
        WHERE {where}
          AND soi.plan IS NOT NULL AND soi.plan != ''
        GROUP BY so.name, soi.name
        ORDER BY so.transaction_date DESC
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

    # Aggregate by sales order for chart
    so_map = {}
    for row in data:
        key = row["sales_order"]
        if key not in so_map:
            so_map[key] = {"actual": 0, "discloseable": 0, "gap": 0}
        so_map[key]["actual"]       += row.get("actual_amount", 0)
        so_map[key]["discloseable"] += row.get("discloseable_amount", 0)
        so_map[key]["gap"]          += row.get("price_gap", 0)

    labels      = list(so_map.keys())[:20]
    actual      = [so_map[k]["actual"] for k in labels]
    discloseable= [so_map[k]["discloseable"] for k in labels]
    gap         = [so_map[k]["gap"] for k in labels]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Actual Amount",       "values": actual},
                {"name": "Discloseable Amount", "values": discloseable},
                {"name": "Price Gap",           "values": gap},
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff", "#00bfa5", "#ff5858"],
    }


def get_summary(data):
    if not data:
        return []

    total_actual       = sum(r.get("actual_amount", 0)       for r in data)
    total_discloseable = sum(r.get("discloseable_amount", 0) for r in data)
    total_gap          = sum(r.get("price_gap", 0)           for r in data)
    avg_margin         = (total_gap / total_actual * 100) if total_actual else 0

    return [
        {"label": _("Total Actual Revenue"),       "value": total_actual,       "datatype": "Currency", "indicator": "blue"},
        {"label": _("Total Discloseable Revenue"), "value": total_discloseable, "datatype": "Currency", "indicator": "green"},
        {"label": _("Total Price Gap"),            "value": total_gap,          "datatype": "Currency", "indicator": "orange"},
        {"label": _("Average Margin %"),           "value": round(avg_margin, 2),"datatype": "Percent", "indicator": "purple"},
    ]
