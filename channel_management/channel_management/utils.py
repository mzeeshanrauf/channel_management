import frappe


def get_sales_person_for_user(user=None):
    """
    Return the Sales Person name linked to a given user.
    Looks up via the user_id field added directly on the Sales Person doctype.
    """
    if not user:
        user = frappe.session.user

    return frappe.db.get_value("Sales Person", {"user_id": user}, "name") or None
