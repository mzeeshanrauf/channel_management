app_name = "channel_management"
app_title = "Channel Management"
app_publisher = "ErpTronix"
app_description = "DU Channel Partner SME Plan Management"
app_email = "info@erptronix.com"
app_license = "MIT"
app_version = "1.0.0"

# ─── Fixtures ─────────────────────────────────────────────────────────────────
fixtures = [
    {"doctype": "Role", "filters": [["name", "in", ["Channel Sales", "Channel Manager"]]]},
    {"doctype": "Workflow", "filters": [["name", "=", "Sales Form Approval"]]},
    {"doctype": "Workflow State", "filters": [["workflow_state_name", "in", [
        "Draft", "Pending Approval", "Approved", "Rejected"
    ]]]},
    {"doctype": "Workflow Action Master", "filters": [["name", "in", [
        "Submit for Approval", "Approve", "Reject", "Resubmit"
    ]]]},
]

# ─── Scheduled Tasks ─────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "channel_management.channel_management.tasks.daily.update_plan_statuses",
        "channel_management.channel_management.tasks.daily.update_kpi_achievements",
    ]
}

# ─── Installation ─────────────────────────────────────────────────────────────
after_install = "channel_management.channel_management.install.after_install"
after_migrate = "channel_management.channel_management.install.after_install"

# ─── Permissions ─────────────────────────────────────────────────────────────
has_permission = {
    "Sales Form":    "channel_management.channel_management.permissions.sales_form.has_permission",
    "Customer Plan": "channel_management.channel_management.permissions.customer_plan.has_permission",
    "KPI Target":    "channel_management.channel_management.permissions.kpi_target.has_permission",
    "Customer":      "channel_management.channel_management.permissions.customer.has_permission",
}

# ─── Assets ───────────────────────────────────────────────────────────────────
app_include_css = ["/assets/channel_management/css/channel_management.css"]

doctype_js = {
    "Sales Form": "public/js/sales_form.js",
}
