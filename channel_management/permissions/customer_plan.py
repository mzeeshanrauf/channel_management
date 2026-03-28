import frappe


def has_permission(doc, ptype="read", user=None):
    """
    Sales team can only see Customer Plans linked to their own Sales Orders.
    Managers can see all.
    """
    if not user:
        user = frappe.session.user

    if frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user):
        return True

    if frappe.has_role("Channel Sales", user=user):
        if ptype in ("create", "write", "delete", "submit", "cancel"):
            return False

        # Only see plans where the sales order's sales team includes them
        if doc.sales_order:
            sales_person = _get_sales_person_for_user(user)
            if not sales_person:
                return False
            return frappe.db.exists(
                "Sales Team",
                {"parent": doc.sales_order, "sales_person": sales_person}
            )
        return False

    return False


def _get_sales_person_for_user(user):
    """Return the Sales Person linked to the given ERPNext user."""
    return frappe.db.get_value("Sales Person", {"user_id": user}, "name")
