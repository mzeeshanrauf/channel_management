import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    create_roles()
    create_customer_custom_fields()
    create_workflow()
    frappe.db.commit()
    print("✅ Channel Management installed successfully.")


# ─── Roles ────────────────────────────────────────────────────────────────────

def create_roles():
    for role_name, desc in [
        ("Channel Sales",   "DU Channel Partner Sales Team Member"),
        ("Channel Manager", "DU Channel Partner Manager"),
    ]:
        if not frappe.db.exists("Role", role_name):
            doc = frappe.new_doc("Role")
            doc.role_name   = role_name
            doc.desk_access = 1
            doc.description = desc
            doc.insert(ignore_permissions=True)
            print(f"  Created role: {role_name}")


# ─── Customer Custom Fields ───────────────────────────────────────────────────

def create_customer_custom_fields():
    """Add channel-specific fields to Customer for manager filtering."""
    fields = {
        "Customer": [
            {
                "fieldname": "channel_section",
                "label": "Channel Info",
                "fieldtype": "Section Break",
                "insert_after": "customer_name",
                "collapsible": 1,
            },
            {
                "fieldname": "assigned_sales_person",
                "label": "Assigned Sales Person",
                "fieldtype": "Link",
                "options": "Sales Person",
                "insert_after": "channel_section",
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "channel_col_break",
                "fieldtype": "Column Break",
                "insert_after": "assigned_sales_person",
            },
            {
                "fieldname": "customer_company",
                "label": "Company Name",
                "fieldtype": "Data",
                "insert_after": "channel_col_break",
                "in_standard_filter": 1,
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)


# ─── Workflow ─────────────────────────────────────────────────────────────────

def create_workflow():
    """Create the Sales Form approval workflow."""
    if frappe.db.exists("Workflow", "Sales Form Approval"):
        return

    # Create workflow states
    states = [
    ('Draft', 'Secondary', 'Edit'),          # or ""
    ('Pending Approval', 'Warning', ''),
    ('Approved', 'Success', ''),
    ('Rejected', 'Danger', 'Edit')
]
    for state_name, style, allow_edit in states:
        if not frappe.db.exists("Workflow State", state_name):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = state_name
            doc.style              = style
            doc.insert(ignore_permissions=True)

    # Create workflow actions
    actions = ["Submit for Approval", "Approve", "Reject", "Resubmit"]
    for action in actions:
        if not frappe.db.exists("Workflow Action Master", action):
            doc = frappe.new_doc("Workflow Action Master")
            doc.workflow_action_name = action
            doc.insert(ignore_permissions=True)

    # Create workflow
    wf = frappe.new_doc("Workflow")
    wf.workflow_name    = "Sales Form Approval"
    wf.document_type    = "Sales Form"
    wf.is_active        = 1
    wf.send_email_alert = 0
    wf.workflow_state_field = "workflow_state"

    wf.states = []
    state_configs = [
        ("Draft",            "Draft",            "Channel Sales",   1),
        ("Pending Approval", "Pending Approval",  "Channel Manager", 0),
        ("Approved",         "Approved",          "Channel Manager", 0),
        ("Rejected",         "Rejected",          "Channel Sales",   1),
    ]
    for state, doc_status_label, allow_edit_role, is_optional_state in state_configs:
        wf.append("states", {
            "state":           state,
            "doc_status":      "0" if state in ["Draft", "Rejected"] else ("1" if state == "Approved" else "0"),
            "allow_edit":      allow_edit_role,
            "is_optional_state": is_optional_state,
        })

    wf.transitions = []
    transitions = [
        ("Draft",            "Submit for Approval", "Pending Approval", "Channel Sales",   ""),
        ("Pending Approval", "Approve",             "Approved",          "Channel Manager", ""),
        ("Pending Approval", "Reject",              "Rejected",          "Channel Manager", ""),
        ("Rejected",         "Resubmit",            "Pending Approval",  "Channel Sales",   ""),
    ]
    for from_state, action, next_state, allowed, condition in transitions:
        wf.append("transitions", {
            "state":       from_state,
            "action":      action,
            "next_state":  next_state,
            "allowed":     allowed,
            "condition":   condition,
        })

    wf.insert(ignore_permissions=True)
    print("  Created workflow: Sales Form Approval")
