import frappe


def has_permission(doc, ptype="read", user=None):
    """
    Sales team can only see their own KPI Targets.
    Managers can see all and write.
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

        return doc.sales_person == sales_person

    return False
