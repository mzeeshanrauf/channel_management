def after_install():
    create_roles()
    create_customer_custom_fields()
    create_workflow()
    frappe.db.commit()
    print("✅ Channel Management installed successfully.")
    
def create_workflow():
    """Create the Sales Form approval workflow."""
    if frappe.db.exists("Workflow", "Sales Form Approval"):
        return

    # Create workflow states
    states = [
        ('Draft', '', 'Edit'),
        ('Pending Approval', 'Warning', ''),
        ('Approved', 'Success', ''),
        ('Rejected', 'Danger', 'Edit')
    ]

    for state_name, style, allow_edit in states:
        if not frappe.db.exists("Workflow State", state_name):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = state_name
            doc.style = style
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
    wf.workflow_name = "Sales Form Approval"
    wf.document_type = "Sales Form"
    wf.is_active = 1
    wf.send_email_alert = 0
    wf.workflow_state_field = "workflow_state"

    wf.states = []
    state_configs = [
        ("Draft", "Channel Sales", 0),
        ("Pending Approval", "Channel Manager", 0),
        ("Approved", "Channel Manager", 1),
        ("Rejected", "Channel Sales", 0),
    ]

    for state, role, docstatus in state_configs:
        wf.append("states", {
            "state": state,
            "doc_status": docstatus,
            "allow_edit": role,
        })

    wf.transitions = []
    transitions = [
        ("Draft", "Submit for Approval", "Pending Approval", "Channel Sales"),
        ("Pending Approval", "Approve", "Approved", "Channel Manager"),
        ("Pending Approval", "Reject", "Rejected", "Channel Manager"),
        ("Rejected", "Resubmit", "Pending Approval", "Channel Sales"),
    ]

    for from_state, action, next_state, allowed in transitions:
        wf.append("transitions", {
            "state": from_state,
            "action": action,
            "next_state": next_state,
            "allowed": allowed,
        })

    wf.insert(ignore_permissions=True)
    print("  Created workflow: Sales Form Approval")