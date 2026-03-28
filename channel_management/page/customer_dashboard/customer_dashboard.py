import frappe
from frappe import _


def get_context(context):
    context.title = "Customer Dashboard"


@frappe.whitelist()
def get_customer_plan_summary(customer):
    """
    Returns a summary of plans for the given customer:
    - Total active plans
    - Plans expiring soon
    - Plans requiring renewal
    - Expired plans
    - Full plan details list
    """
    frappe.has_permission("Customer Plan", throw=True)

    plans = frappe.db.sql("""
        SELECT
            cp.name,
            cp.plan,
            pm.plan_category,
            cp.start_date,
            cp.end_date,
            cp.status,
            cp.days_to_expiry,
            cp.sales_order,
            cp.sales_person,
            cp.discloseable_rate_snapshot
        FROM `tabCustomer Plan` cp
        LEFT JOIN `tabPlan Master` pm ON pm.name = cp.plan
        WHERE cp.customer = %s
          AND cp.status != 'Cancelled'
        ORDER BY cp.end_date ASC
    """, (customer,), as_dict=True)

    # Counts
    summary = {
        "total":            len(plans),
        "active":           sum(1 for p in plans if p.status == "Active"),
        "expiring_soon":    sum(1 for p in plans if p.status == "Expiring Soon"),
        "renewal_required": sum(1 for p in plans if p.status == "Renewal Required"),
        "expired":          sum(1 for p in plans if p.status == "Expired"),
        "plans":            plans,
    }

    # Customer details
    customer_doc = frappe.db.get_value(
        "Customer",
        customer,
        ["customer_name", "customer_type", "mobile_no", "email_id", "territory", "customer_group"],
        as_dict=True
    )
    summary["customer"] = customer_doc

    return summary


@frappe.whitelist()
def get_all_customers_with_plans():
    """Returns distinct customers who have at least one Customer Plan."""
    user       = frappe.session.user
    is_manager = frappe.has_role("Channel Manager", user=user)
    is_admin   = frappe.has_role("Administrator",   user=user)

    conditions = ""
    values     = []

    if not (is_manager or is_admin):
        sp = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if not sp:
            return []
        conditions = "AND cp.sales_person = %s"
        values.append(sp)

    return frappe.db.sql(f"""
        SELECT DISTINCT cp.customer, c.customer_name
        FROM `tabCustomer Plan` cp
        JOIN `tabCustomer` c ON c.name = cp.customer
        WHERE cp.status != 'Cancelled'
        {conditions}
        ORDER BY c.customer_name
    """, values, as_dict=True)
