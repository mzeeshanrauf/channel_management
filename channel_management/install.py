import frappe


def after_install():
    create_roles()
    create_customer_custom_fields()
    create_workflow()
    frappe.db.commit()
    print("✅ Channel Management installed successfully.")


def create_roles():
    """Create custom roles if they don't exist."""
    for role_name in ["Channel Sales", "Channel Manager"]:
        if not frappe.db.exists("Role", role_name):
            doc = frappe.new_doc("Role")
            doc.role_name = role_name
            doc.desk_access = 1
            doc.insert(ignore_permissions=True)
            print(f"  Created role: {role_name}")


def create_customer_custom_fields():
    """Add assigned_sales_person custom field to Customer doctype."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    custom_fields = {
        "Customer": [
            {
                "fieldname": "assigned_sales_person",
                "label": "Assigned Sales Person",
                "fieldtype": "Link",
                "options": "Sales Person",
                "insert_after": "territory",
                "in_list_view": 0,
                "search_index": 1,
            }
        ]
    }
    create_custom_fields(custom_fields, ignore_validate=True)
    print("  Created custom field: Customer.assigned_sales_person")


def create_workflow():
    """Create the Sales Form approval workflow."""
    if frappe.db.exists("Workflow", "Sales Form Approval"):
        return

    # Create workflow states
    states = [
        ("Draft",            "",        "Edit"),
        ("Pending Approval", "Warning", ""),
        ("Approved",         "Success", ""),
        ("Rejected",         "Danger",  "Edit"),
    ]
    for state_name, style, allow_edit in states:
        if not frappe.db.exists("Workflow State", state_name):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = state_name
            doc.style = style
            doc.insert(ignore_permissions=True)

    # Create workflow actions
    for action in ["Submit for Approval", "Approve", "Reject", "Resubmit"]:
        if not frappe.db.exists("Workflow Action Master", action):
            doc = frappe.new_doc("Workflow Action Master")
            doc.workflow_action_name = action
            doc.insert(ignore_permissions=True)

    # Create workflow document
    wf = frappe.new_doc("Workflow")
    wf.workflow_name        = "Sales Form Approval"
    wf.document_type        = "Sales Form"
    wf.is_active            = 1
    wf.send_email_alert     = 0
    wf.workflow_state_field = "workflow_state"

    state_configs = [
        ("Draft",            "Channel Sales",   "0"),
        ("Pending Approval", "Channel Manager", "0"),
        ("Approved",         "Channel Manager", "1"),
        ("Rejected",         "Channel Sales",   "0"),
    ]
    for state, role, docstatus in state_configs:
        wf.append("states", {
            "state":      state,
            "doc_status": docstatus,   # must be string "0"/"1" not int
            "allow_edit": role,
        })

    transitions = [
        ("Draft",            "Submit for Approval", "Pending Approval", "Channel Sales"),
        ("Pending Approval", "Approve",             "Approved",         "Channel Manager"),
        ("Pending Approval", "Reject",              "Rejected",         "Channel Manager"),
        ("Rejected",         "Resubmit",            "Pending Approval", "Channel Sales"),
    ]
    for from_state, action, next_state, allowed in transitions:
        wf.append("transitions", {
            "state":      from_state,
            "action":     action,
            "next_state": next_state,
            "allowed":    allowed,
        })

    wf.insert(ignore_permissions=True)
    print("  Created workflow: Sales Form Approval")
