frappe.query_reports["KPI Report"] = {
	filters: [
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
			depends_on: "eval:frappe.user.has_role('Channel Manager') || frappe.user.has_role('Administrator')",
		},
		{
			fieldname: "kpi_type",
			label: __("KPI Type"),
			fieldtype: "Select",
			options: "\nRevenue\nSales Count\nRenewals",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],
};
