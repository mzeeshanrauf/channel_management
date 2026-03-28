from frappe import _


def get_data():
    return [
        {
            "module_name": "Channel Management",
            "color": "#5e64ff",
            "icon": "octicon octicon-broadcast",
            "type": "module",
            "label": _("Channel Management"),
            "description": _("DU SME Plan tracking, dual pricing, KPIs and renewals"),
        }
    ]
