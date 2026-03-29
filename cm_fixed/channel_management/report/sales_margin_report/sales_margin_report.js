frappe.query_reports["Sales Margin Report"] = {
	filters: [
		{fieldname: "from_date",    label: __("From Date"),    fieldtype: "Date",   default: frappe.datetime.month_start()},
		{fieldname: "to_date",      label: __("To Date"),      fieldtype: "Date",   default: frappe.datetime.get_today()},
		{fieldname: "customer",     label: __("Customer"),     fieldtype: "Link",   options: "Customer"},
		{fieldname: "sales_person", label: __("Sales Person"), fieldtype: "Link",   options: "Sales Person"},
		{fieldname: "plan",         label: __("Plan"),         fieldtype: "Link",   options: "Plan Master"},
	],
};
