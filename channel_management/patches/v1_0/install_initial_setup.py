import frappe


def execute():
    from channel_management.channel_management.install import create_roles, create_customer_custom_fields
    create_roles()
    create_customer_custom_fields()
    frappe.db.commit()
    print("  ✅ Channel Management v1.0 patch applied.")
