frappe.query_reports["KPI Report"] = {
    filters: [
        {
            fieldname: "sales_person",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person",
        },
        {
            fieldname: "kpi_type",
            label: __("KPI Type"),
            fieldtype: "Select",
            options: "\nRevenue\nSales Count\nRenewals",
        },
        {
            fieldname: "period_type",
            label: __("Period Type"),
            fieldtype: "Select",
            options: "\nMonthly\nQuarterly\nYearly",
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
        },
    ],

    onload: function(report) {
        // Hide sales_person filter for non-managers
        frappe.call({
            method: "frappe.client.get_value",
            args: { doctype: "User", filters: { name: frappe.session.user }, fieldname: ["name"] },
            callback: function() {
                if (!frappe.user.has_role("Channel Manager") && !frappe.user.has_role("Administrator")) {
                    report.set_filter_value("sales_person", "");
                    // Disable filter so sales can't browse others
                    let spFilter = report.page.fields_dict["sales_person"];
                    if (spFilter) spFilter.df.hidden = 1;
                    report.refresh();
                }
            }
        });
    }
};
