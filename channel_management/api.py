import frappe
from frappe import _


@frappe.whitelist()
def get_pricing_for_plan(plan, partner=None):
    """
    Public API: Returns pricing (discloseable only for sales, full for managers).
    Called from Sales Order form JS to auto-fill pricing fields.
    """
    from channel_management.events.sales_order import _get_channel_pricing

    pricing = _get_channel_pricing(plan, partner)
    if not pricing:
        return None

    user       = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user)

    result = {"discloseable_price": pricing["discloseable_price"]}
    if is_manager:
        result["actual_price"] = pricing["actual_price"]
        result["price_gap"]    = pricing["actual_price"] - pricing["discloseable_price"]

    return result


@frappe.whitelist()
def get_customer_plan_status_counts():
    """
    Returns counts of plans by status for the current user.
    Used by dashboard number cards.
    """
    user       = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user)

    conditions = ""
    values     = []

    if not is_manager:
        sp = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if sp:
            conditions = "AND sales_person = %s"
            values.append(sp)

    result = frappe.db.sql(f"""
        SELECT status, COUNT(*) AS count
        FROM `tabCustomer Plan`
        WHERE status != 'Cancelled'
        {conditions}
        GROUP BY status
    """, values, as_dict=True)

    counts = {
        "Active": 0,
        "Expiring Soon": 0,
        "Renewal Required": 0,
        "Expired": 0,
    }
    for row in result:
        if row.status in counts:
            counts[row.status] = row.count

    return counts


@frappe.whitelist()
def get_my_kpi_summary():
    """
    Returns KPI summary for the currently logged-in sales person.
    Managers get all; sales get their own.
    """
    from frappe.utils import today, getdate

    user       = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user)

    today_date = getdate(today())

    filters = {
        "period_start": ["<=", today_date],
        "period_end":   [">=", today_date],
    }

    if not is_manager:
        sp = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if not sp:
            return []
        filters["sales_person"] = sp

    return frappe.get_all(
        "KPI Target",
        filters=filters,
        fields=["sales_person", "kpi_type", "period_label", "target_value",
                "achieved_value", "achievement_percentage", "status"],
        order_by="achievement_percentage asc",
    )
