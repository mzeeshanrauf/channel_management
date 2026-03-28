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
    allowed = (
        frappe.has_role("Channel Manager", user=user)
        or frappe.has_role("Channel Sales",   user=user)
        or frappe.has_role("Administrator",   user=user)
    )
    if not allowed:
        frappe.throw(_("You do not have permission to view this report."), frappe.PermissionError)


def get_columns():
    return [
        {"label": _("Customer Plan"),   "fieldname": "name",          "fieldtype": "Link",    "options": "Customer Plan", "width": 140},
        {"label": _("Customer"),        "fieldname": "customer",      "fieldtype": "Link",    "options": "Customer",      "width": 160},
        {"label": _("Plan"),            "fieldname": "plan",          "fieldtype": "Link",    "options": "Plan Master",   "width": 150},
        {"label": _("Sales Person"),    "fieldname": "sales_person",  "fieldtype": "Link",    "options": "Sales Person",  "width": 140},
        {"label": _("Start Date"),      "fieldname": "start_date",    "fieldtype": "Date",    "width": 100},
        {"label": _("End Date"),        "fieldname": "end_date",      "fieldtype": "Date",    "width": 100},
        {"label": _("Days to Expiry"),  "fieldname": "days_to_expiry","fieldtype": "Int",     "width": 120},
        {"label": _("Status"),          "fieldname": "status",        "fieldtype": "Data",    "width": 140},
        {"label": _("Sales Order"),     "fieldname": "sales_order",   "fieldtype": "Link",    "options": "Sales Order",   "width": 140},
    ]


def get_data(filters):
    user       = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user)
    is_admin   = frappe.has_role("Administrator",   user=user)

    conditions = []
    values     = {}

    # Default: show expiring/renewal/expired unless overridden
    status_filter = filters.get("status")
    if status_filter:
        conditions.append("cp.status = %(status)s")
        values["status"] = status_filter
    else:
        conditions.append("cp.status IN ('Expiring Soon', 'Renewal Required', 'Expired')")

    if filters.get("customer"):
        conditions.append("cp.customer = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("plan"):
        conditions.append("cp.plan = %(plan)s")
        values["plan"] = filters["plan"]

    # Sales team: only see their own
    if not (is_manager or is_admin):
        sp = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if not sp:
            return []
        conditions.append("cp.sales_person = %(sp)s")
        values["sp"] = sp
    elif filters.get("sales_person"):
        conditions.append("cp.sales_person = %(sales_person)s")
        values["sales_person"] = filters["sales_person"]

    if filters.get("from_date"):
        conditions.append("cp.end_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("cp.end_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    data = frappe.db.sql(f"""
        SELECT
            cp.name,
            cp.customer,
            cp.plan,
            cp.sales_person,
            cp.start_date,
            cp.end_date,
            cp.days_to_expiry,
            cp.status,
            cp.sales_order
        FROM `tabCustomer Plan` cp
        {where}
        ORDER BY cp.days_to_expiry ASC
    """, values, as_dict=True)

    # Format status with color indicators
    for row in data:
        if row.status == "Renewal Required":
            row["status"] = "<span style='color:red;font-weight:bold'>🔴 Renewal Required</span>"
        elif row.status == "Expiring Soon":
            row["status"] = "<span style='color:orange;font-weight:bold'>🟠 Expiring Soon</span>"
        elif row.status == "Expired":
            row["status"] = "<span style='color:#888;font-weight:bold'>⚫ Expired</span>"
        elif row.status == "Active":
            row["status"] = "<span style='color:green;font-weight:bold'>🟢 Active</span>"

    return data


def get_chart(data):
    if not data:
        return None

    status_counts = {"Renewal Required": 0, "Expiring Soon": 0, "Expired": 0, "Active": 0}
    for row in data:
        raw = row.get("status", "")
        for key in status_counts:
            if key in raw:
                status_counts[key] += 1
                break

    return {
        "data": {
            "labels": list(status_counts.keys()),
            "datasets": [{"values": list(status_counts.values())}]
        },
        "type": "donut",
        "colors": ["#ff5858", "#ff9800", "#9e9e9e", "#00bfa5"],
    }


def get_summary(data):
    renewal_req  = sum(1 for r in data if "Renewal Required" in str(r.get("status", "")))
    expiring     = sum(1 for r in data if "Expiring Soon"    in str(r.get("status", "")))
    expired      = sum(1 for r in data if "Expired"          in str(r.get("status", "")))

    return [
        {"label": _("Renewal Required"), "value": renewal_req, "datatype": "Int", "indicator": "red"},
        {"label": _("Expiring Soon"),    "value": expiring,    "datatype": "Int", "indicator": "orange"},
        {"label": _("Expired"),          "value": expired,     "datatype": "Int", "indicator": "grey"},
    ]
