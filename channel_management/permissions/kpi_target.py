import frappe


def has_permission(doc, ptype="read", user=None):
    """
    Frappe v16: must explicitly return True to grant permission.
    Sales team: only see their own KPI Targets.
    Managers: see all and write.
    """
    if not user:
        user = frappe.session.user

    if frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user):
        return True

    if frappe.has_role("Channel Sales", user=user):
        if ptype in ("create", "write", "delete"):
            return False

        sales_person = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if not sales_person:
            return False

        return True if doc.sales_person == sales_person else False

    return False
