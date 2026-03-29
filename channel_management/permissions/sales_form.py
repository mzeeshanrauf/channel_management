import frappe
from channel_management.utils import get_sales_person_for_user


def has_permission(doc, ptype="read", user=None):
    if not user:
        user = frappe.session.user
    if user == "Guest":
        return False
    if ("Channel Manager" in frappe.get_roles(user)) or ("Administrator" in frappe.get_roles(user)):
        return True
    if ("Channel Sales" in frappe.get_roles(user)):
        if ptype == "delete":
            return False
        sp = get_sales_person_for_user(user)
        if not sp:
            return False
        return doc.sales_person == sp
    return False
