import frappe
from frappe import _
from channel_management.utils import get_sales_person_for_user


@frappe.whitelist()
def get_sales_person_for_user_api():
    """Get Sales Person linked to logged-in user (ERPNext v15 compatible)."""
    return get_sales_person_for_user(frappe.session.user)


@frappe.whitelist()
def get_pricing_for_plan(plan, partner=None):
    """
    Get Channel Pricing for a plan.
    Managers see actual_price. Sales see only sale_amount (discloseable).
    """
    from channel_management.channel_management.doctype.sales_form.sales_form import get_channel_pricing

    pricing = get_channel_pricing(plan, partner)
    if not pricing:
        return None

    user       = frappe.session.user
    is_manager = (
        ("Channel Manager" in frappe.get_roles(user)) or
        ("Administrator" in frappe.get_roles(user))
    )

    return {
        "sale_amount":   float(pricing["discloseable_price"] or 0),
        "actual_amount": float(pricing["actual_price"] or 0) if is_manager else float(pricing["discloseable_price"] or 0),
        "price_gap":     float(pricing["actual_price"] - pricing["discloseable_price"]) if is_manager else 0,
        "is_manager":    is_manager,
    }


@frappe.whitelist()
def get_customer_plan_summary(customer):
    """Get plan summary for a customer."""
    frappe.has_permission("Customer Plan", throw=True)

    user       = frappe.session.user
    is_manager = (
        ("Channel Manager" in frappe.get_roles(user)) or
        ("Administrator" in frappe.get_roles(user))
    )

    # For sales, verify they are assigned to this customer
    if not is_manager:
        sp = get_sales_person_for_user(user)
        assigned_sp = frappe.db.get_value("Customer", customer, "assigned_sales_person")
        if sp != assigned_sp:
            frappe.throw(_("Not permitted to view this customer's plans."), frappe.PermissionError)

    plans = frappe.db.sql("""
        SELECT cp.name, cp.plan, cp.start_date, cp.end_date,
               cp.status, cp.days_to_expiry, cp.sales_form,
               cp.sales_person, cp.sale_amount_snapshot,
               cp.actual_amount_snapshot
        FROM `tabCustomer Plan` cp
        WHERE cp.customer = %s AND cp.status != 'Cancelled'
        ORDER BY cp.end_date ASC
    """, (customer,), as_dict=True)

    # Hide actual_amount from sales
    if not is_manager:
        for p in plans:
            p.pop("actual_amount_snapshot", None)

    customer_doc = frappe.db.get_value(
        "Customer", customer,
        ["customer_name", "mobile_no", "email_id", "customer_group", "territory", "assigned_sales_person"],
        as_dict=True
    )

    return {
        "customer":         customer_doc,
        "total":            len(plans),
        "active":           sum(1 for p in plans if p.status == "Active"),
        "expiring_soon":    sum(1 for p in plans if p.status == "Expiring Soon"),
        "renewal_required": sum(1 for p in plans if p.status == "Renewal Required"),
        "expired":          sum(1 for p in plans if p.status == "Expired"),
        "plans":            plans,
        "is_manager":       is_manager,
    }


@frappe.whitelist()
def get_my_customers():
    """Get customers assigned to the logged-in sales person."""
    user = frappe.session.user
    sp   = get_sales_person_for_user(user)
    if not sp:
        return []

    return frappe.get_all(
        "Customer",
        filters={"assigned_sales_person": sp},
        fields=["name", "customer_name", "mobile_no", "email_id"],
        order_by="customer_name asc",
    )


@frappe.whitelist()
def get_dashboard_stats():
    """Get stats for the channel management dashboard."""
    user       = frappe.session.user
    is_manager = (
        ("Channel Manager" in frappe.get_roles(user)) or
        ("Administrator" in frappe.get_roles(user))
    )

    sp_filter = ""
    values    = []

    if not is_manager:
        sp = get_sales_person_for_user(user)
        if sp:
            sp_filter = "AND sales_person = %s"
            values.append(sp)

    # Plan status counts
    plan_counts = frappe.db.sql(f"""
        SELECT status, COUNT(*) as count
        FROM `tabCustomer Plan`
        WHERE status != 'Cancelled' {sp_filter}
        GROUP BY status
    """, values, as_dict=True)

    # Sales form counts
    form_counts = frappe.db.sql(f"""
        SELECT workflow_state, COUNT(*) as count
        FROM `tabSales Form`
        WHERE 1=1 {sp_filter}
        GROUP BY workflow_state
    """, values, as_dict=True)

    return {
        "plan_counts": plan_counts,
        "form_counts": form_counts,
        "is_manager":  is_manager,
    }
