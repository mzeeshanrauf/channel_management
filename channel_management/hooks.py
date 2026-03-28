app_name = "channel_management"
app_title = "Channel Management"
app_publisher = "ErpTronix"
app_description = "DU Channel Partner SME Plan Management with Dual Pricing, KPI Tracking and Renewal Alerts"
app_email = "info@erptronix.com"
app_license = "MIT"
app_version = "1.0.0"

# ─── DocType Fixtures ────────────────────────────────────────────────────────
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "Channel Management"]]
    },
    {
        "doctype": "Property Setter",
        "filters": [["module", "=", "Channel Management"]]
    },
    {
        "doctype": "Role",
        "filters": [["name", "in", ["Channel Sales", "Channel Manager"]]]
    },
]

# ─── Document Events ─────────────────────────────────────────────────────────
doc_events = {
    "Sales Order": {
        "validate":  "channel_management.events.sales_order.on_validate",
        "on_submit": "channel_management.events.sales_order.on_submit",
        "on_cancel": "channel_management.events.sales_order.on_cancel",
    }
}

# ─── Scheduled Tasks ─────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "channel_management.tasks.daily.update_plan_statuses",
        "channel_management.tasks.daily.update_kpi_achievements",
    ]
}

# ─── Installation ─────────────────────────────────────────────────────────────
after_install = "channel_management.install.after_install"
after_migrate = "channel_management.install.after_install"

# ─── Permissions ─────────────────────────────────────────────────────────────
has_permission = {
    "Customer Plan": "channel_management.permissions.customer_plan.has_permission",
    "KPI Target":    "channel_management.permissions.kpi_target.has_permission",
}

# ─── Static Assets ────────────────────────────────────────────────────────────
# CSS served directly — no esbuild required
app_include_css = ["/assets/channel_management/css/channel_management.css"]

# JS bundle — esbuild auto-discovers *.bundle.js files in public/
# NOTE: app_include_js is intentionally removed.
# The Sales Order JS is loaded via doctype_js (Frappe's own pipeline, no esbuild).
# Role injection is handled inside the doctype JS itself.

# ─── DocType Client Scripts ────────────────────────────────────────────────────
doctype_js = {
    "Sales Order": "public/js/sales_order.js",
}

# ─── Report Permissions ───────────────────────────────────────────────────────
# Enforced inside each report's .py file via role checks
