import frappe


def execute():
    """
    v1.0 initial setup patch.
    Ensures roles and custom fields are present after migrate.
    """
    from channel_management.install import (
        create_roles,
        create_custom_fields_on_sales_order,
        create_custom_fields_on_sales_order_item,
    )

    create_roles()
    create_custom_fields_on_sales_order()
    create_custom_fields_on_sales_order_item()
    frappe.db.commit()
    print("  ✅ Channel Management v1.0 patch applied.")
