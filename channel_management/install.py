import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    """Run after app install or migrate."""
    create_roles()
    create_custom_fields_on_sales_order()
    create_custom_fields_on_sales_order_item()
    print("✅ Channel Management app installed successfully.")


# ─── Roles ───────────────────────────────────────────────────────────────────

def create_roles():
    roles = [
        {
            "role_name": "Channel Sales",
            "desk_access": 1,
            "description": "DU Channel Partner Sales Team Member"
        },
        {
            "role_name": "Channel Manager",
            "desk_access": 1,
            "description": "DU Channel Partner Manager / Management"
        },
    ]
    for r in roles:
        if not frappe.db.exists("Role", r["role_name"]):
            doc = frappe.new_doc("Role")
            doc.role_name = r["role_name"]
            doc.desk_access = r["desk_access"]
            doc.description = r["description"]
            doc.insert(ignore_permissions=True)
            print(f"  Created role: {r['role_name']}")


# ─── Custom Fields ────────────────────────────────────────────────────────────

def create_custom_fields_on_sales_order():
    """Add channel fields on Sales Order header."""
    fields = {
        "Sales Order": [
            {
                "fieldname": "channel_section",
                "label": "Channel Pricing",
                "fieldtype": "Section Break",
                "insert_after": "selling_price_list",
                "collapsible": 1,
            },
            {
                "fieldname": "channel_partner",
                "label": "Channel Partner",
                "fieldtype": "Link",
                "options": "Customer",
                "insert_after": "channel_section",
            },
            {
                "fieldname": "channel_col_break",
                "fieldtype": "Column Break",
                "insert_after": "channel_partner",
            },
            {
                "fieldname": "total_discloseable_amount",
                "label": "Total Discloseable Amount",
                "fieldtype": "Currency",
                "insert_after": "channel_col_break",
                "read_only": 1,
                "bold": 1,
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)


def create_custom_fields_on_sales_order_item():
    """Add dual pricing fields to Sales Order Item child table."""
    fields = {
        "Sales Order Item": [
            {
                "fieldname": "channel_pricing_section",
                "label": "Channel Pricing",
                "fieldtype": "Section Break",
                "insert_after": "amount",
                "collapsible": 1,
            },
            {
                "fieldname": "plan",
                "label": "SME Plan",
                "fieldtype": "Link",
                "options": "Plan Master",
                "insert_after": "channel_pricing_section",
            },
            {
                "fieldname": "discloseable_rate",
                "label": "Discloseable Rate",
                "fieldtype": "Currency",
                "insert_after": "plan",
                "read_only": 1,
            },
            {
                "fieldname": "discloseable_amount",
                "label": "Discloseable Amount",
                "fieldtype": "Currency",
                "insert_after": "discloseable_rate",
                "read_only": 1,
            },
            {
                "fieldname": "price_gap",
                "label": "Price Gap",
                "fieldtype": "Currency",
                "insert_after": "discloseable_amount",
                "read_only": 1,
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)
