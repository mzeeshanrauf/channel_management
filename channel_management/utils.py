import frappe


@frappe.whitelist()
def get_sales_person_for_user(user=None):
    """
    Return the Sales Person name linked to a given user.
    Looks up via the user_id field on the Sales Person doctype.
    Whitelisted so it can be called from client scripts.
    """
    if not user:
        user = frappe.session.user

    if user == "Guest":
        return None

    return frappe.db.get_value("Sales Person", {"user_id": user}, "name") or None
