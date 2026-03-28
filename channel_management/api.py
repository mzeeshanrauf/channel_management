import frappe
from frappe import _


@frappe.whitelist()
def get_pricing_for_plan(plan, partner=None):
    """
    Returns pricing for a plan.
    - Managers get both actual_price and discloseable_price
    - Sales get only discloseable_price (actual is set server-side on validate)
    """
    from channel_management.events.sales_order import _get_channel_pricing

    pricing = _get_channel_pricing(plan, partner)
    if not pricing:
        return None

    user       = frappe.session.user
    is_manager = (
        frappe.has_role("Channel Manager", user=user) or
        frappe.has_role("Administrator",   user=user)
    )

    # Always return discloseable price so the JS can populate the field
    result = {
        "discloseable_price": flt(pricing["discloseable_price"]),
        "actual_price":       flt(pricing["actual_price"]),   # needed so rate field gets set
        "price_gap":          flt(pricing["actual_price"]) - flt(pricing["discloseable_price"]),
        "is_manager":         is_manager,
    }

    # For sales users, mask actual_price in the response
    # (server-side on_validate will always use the real actual_price)
    if not is_manager:
        result["actual_price"] = flt(pricing["discloseable_price"])
        result["price_gap"]    = 0

    return result


def flt(val):
    try:
        return float(val or 0)
    except Exception:
        return 0.0


@frappe.whitelist()
def get_customer_plan_status_counts():
    """Returns counts of plans by status for the current user."""
    user       = frappe.session.user
    is_manager = (
        frappe.has_role("Channel Manager", user=user) or
        frappe.has_role("Administrator",   user=user)
    )

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

    counts = {"Active": 0, "Expiring Soon": 0, "Renewal Required": 0, "Expired": 0}
    for row in result:
        if row.status in counts:
            counts[row.status] = row.count

    return counts


@frappe.whitelist()
def get_my_kpi_summary():
    """Returns KPI summary for the logged-in sales person."""
    from frappe.utils import today, getdate

    user       = frappe.session.user
    is_manager = (
        frappe.has_role("Channel Manager", user=user) or
        frappe.has_role("Administrator",   user=user)
    )

    today_date = getdate(today())
    filters    = {
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
        fields=["sales_person", "kpi_type", "period_label",
                "target_value", "achieved_value", "achievement_percentage", "status"],
        order_by="achievement_percentage asc",
    )
