import frappe


@frappe.whitelist()
def get_sales_person_for_user(user=None):
    """
    Return the Sales Person name linked to a given user.

    Uses the standard ERPNext chain:
      User -> Employee (user_id field) -> Sales Person (employee field)

    Falls back to a custom user_id field on Sales Person if it exists.
    """
    if not user:
        user = frappe.session.user

    if not user or user == "Guest":
        return None

    # Standard ERPNext path: User → Employee → Sales Person
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if employee:
        sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
        if sales_person:
            return sales_person

    # Fallback: custom user_id field directly on Sales Person (if added via customization)
    try:
        sales_person = frappe.db.get_value("Sales Person", {"user_id": user}, "name")
        if sales_person:
            return sales_person
    except Exception:
        # Column doesn't exist — custom field not yet created, ignore silently
        pass

    return None
