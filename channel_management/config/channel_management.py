from frappe import _


def get_data():
    return [
        {
            "label": _("Plan Management"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Plan Master",
                    "label": _("Plan Master"),
                    "description": _("Define SME plans and their validity."),
                },
                {
                    "type": "doctype",
                    "name": "Channel Pricing",
                    "label": _("Channel Pricing"),
                    "description": _("Set actual and discloseable prices per plan."),
                },
            ],
        },
        {
            "label": _("Customer Plans"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Customer Plan",
                    "label": _("Customer Plan"),
                    "description": _("Track active, expiring and expired customer plans."),
                },
                {
                    "type": "page",
                    "name": "customer-dashboard",
                    "label": _("Customer Dashboard"),
                    "description": _("View plan summary per customer."),
                },
            ],
        },
        {
            "label": _("KPI & Performance"),
            "items": [
                {
                    "type": "doctype",
                    "name": "KPI Target",
                    "label": _("KPI Target"),
                    "description": _("Set and track sales person KPI targets."),
                },
            ],
        },
        {
            "label": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "KPI Report",
                    "label": _("KPI Report"),
                    "doctype": "KPI Target",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Renewal Report",
                    "label": _("Renewal Report"),
                    "doctype": "Customer Plan",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Sales Margin Report",
                    "label": _("Sales Margin Report"),
                    "doctype": "Sales Order",
                    "is_query_report": True,
                },
            ],
        },
    ]
