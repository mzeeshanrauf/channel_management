import frappe


def has_permission(doc, ptype="read", user=None):
    if not user:
        user = frappe.session.user

    if frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user):
        return True

    if frappe.has_role("Channel Sales", user=user):
        if ptype in ("create", "write", "delete"):
            return False
        sp = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if not sp:
            return False
        return True if doc.sales_person == sp else False

    return False
