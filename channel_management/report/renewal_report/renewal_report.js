frappe.query_reports["Renewal Report"] = {
    filters: [
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: "\nActive\nExpiring Soon\nRenewal Required\nExpired\nCancelled",
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "plan",
            label: __("Plan"),
            fieldtype: "Link",
            options: "Plan Master",
        },
        {
            fieldname: "sales_person",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person",
            depends_on: "eval:frappe.user.has_role('Channel Manager') || frappe.user.has_role('Administrator')",
        },
        {
            fieldname: "from_date",
            label: __("Expiry From"),
            fieldtype: "Date",
        },
        {
            fieldname: "to_date",
            label: __("Expiry To"),
            fieldtype: "Date",
        },
    ],
};
