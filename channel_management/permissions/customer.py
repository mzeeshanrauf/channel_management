import frappe
from channel_management.utils import get_sales_person_for_user


def has_permission(doc, ptype="read", user=None):
    if not user:
        user = frappe.session.user

    if frappe.has_role("Channel Manager", user=user) or frappe.has_role("Administrator", user=user):
        return True

    if frappe.has_role("Channel Sales", user=user):
        if ptype in ("create", "write", "delete"):
            return False

        sp = get_sales_person_for_user(user)
        if not sp:
            return False

        # Sales can only see customers assigned to them
        return True if doc.get("assigned_sales_person") == sp else False

    return False
