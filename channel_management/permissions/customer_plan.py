import frappe


def has_permission(doc, ptype="read", user=None):
    """
    Frappe v16: must explicitly return True to grant permission.
    Sales team: only see Customer Plans linked to their own Sales Orders.
    Managers: see all.
    """
    if not user:
        user = frappe.session.user

    if frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user):
        return True

    if frappe.has_role("Channel Sales", user=user):
        if ptype in ("create", "write", "delete", "submit", "cancel"):
            return False

        sales_person = _get_sales_person_for_user(user)
        if not sales_person:
            return False

        if doc.sales_order:
            exists = frappe.db.exists(
                "Sales Team",
                {"parent": doc.sales_order, "sales_person": sales_person}
            )
            return True if exists else False

        return False

    return False


def _get_sales_person_for_user(user):
    return frappe.db.get_value("Sales Person", {"user_id": user}, "name")
