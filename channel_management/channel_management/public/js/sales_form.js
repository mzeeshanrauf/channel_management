// ─── Channel Management: Sales Form Client Script ───────────────────────────

function cm_is_manager() {
	return frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator");
}

// ── Main Form Events ──────────────────────────────────────────────────────────
frappe.ui.form.on("Sales Form", {

	setup(frm) {
		// Filter customers: sales sees only assigned customers
		if (!cm_is_manager()) {
			frm.set_query("customer", function () {
				return {
					query: "channel_management.api.get_my_customers_query",
				};
			});
		}

		// Filter sales_person: managers can select any, sales sees only themselves
		frm.set_query("sales_person", function () {
			if (cm_is_manager()) return {};
			const sp = frm.doc.__sp_cache;
			if (sp) return { filters: { name: sp } };
			return {};
		});
	},

	onload(frm) {
		if (frm.is_new()) {
			cm_auto_set_sales_person(frm);
		}
		cm_apply_visibility(frm);
	},

	refresh(frm) {
		cm_apply_visibility(frm);
		cm_setup_workflow_buttons(frm);
		cm_add_custom_buttons(frm);
	},

	customer(frm) {
		// Refresh plans section when customer changes
		frm.refresh_field("plans");
	},
});

// ── Plans Child Table Events ───────────────────────────────────────────────────
frappe.ui.form.on("Sales Form Item", {

	plan(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.plan) {
			cm_fetch_pricing(frm, row, cdt, cdn);
		} else {
			frappe.model.set_value(cdt, cdn, "sale_amount",   0);
			frappe.model.set_value(cdt, cdn, "actual_amount", 0);
			frappe.model.set_value(cdt, cdn, "price_gap",     0);
			cm_update_totals(frm);
		}
	},

	start_date(frm, cdt, cdn) {
		cm_update_totals(frm);
	},

	end_date(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.start_date && row.end_date && row.end_date < row.start_date) {
			frappe.model.set_value(cdt, cdn, "end_date", "");
			frappe.show_alert({
				message: __("End Date cannot be before Start Date."),
				indicator: "red"
			});
		}
		cm_update_totals(frm);
	},

	plans_remove(frm) {
		cm_update_totals(frm);
	},
});

// ── Fetch Pricing from Server ──────────────────────────────────────────────────
function cm_fetch_pricing(frm, row, cdt, cdn) {
	if (!row.plan) return;

	frappe.call({
		method: "channel_management.api.get_pricing_for_plan",
		args: { plan: row.plan, partner: frm.doc.customer || null },
		freeze: false,
		callback(r) {
			if (!r || !r.message) {
				frappe.show_alert({
					message: __("No active Channel Pricing for plan: {0}", [row.plan]),
					indicator: "orange"
				});
				return;
			}

			const p = r.message;

			frappe.model.set_value(cdt, cdn, "sale_amount",   flt(p.sale_amount));
			frappe.model.set_value(cdt, cdn, "actual_amount", flt(p.actual_amount));
			frappe.model.set_value(cdt, cdn, "price_gap",     flt(p.price_gap));

			cm_update_totals(frm);
			frm.refresh_field("plans");
		},
		error() {
			frappe.show_alert({
				message: __("Error fetching pricing. Check Channel Pricing setup."),
				indicator: "red"
			});
		}
	});
}

// ── Auto-set Sales Person ──────────────────────────────────────────────────────
function cm_auto_set_sales_person(frm) {
	frappe.call({
		method: "channel_management.api.get_sales_person_for_user",
		callback(r) {
			if (!r.message) return;
			const sp = r.message;
			frm.__sp_cache = sp;

			if (!frm.doc.sales_person) {
				frm.set_value("sales_person", sp);
			}
		}
	});
}

// ── Calculate and update totals ────────────────────────────────────────────────
function cm_update_totals(frm) {
	let total_sale   = 0;
	let total_actual = 0;
	let total_gap    = 0;

	(frm.doc.plans || []).forEach(row => {
		total_sale   += flt(row.sale_amount);
		total_actual += flt(row.actual_amount);
		total_gap    += flt(row.price_gap);
	});

	frm.set_value("total_sale_amount",   total_sale);
	frm.set_value("total_actual_amount", total_actual);
	frm.set_value("total_price_gap",     total_gap);
}

// ── Apply Field Visibility Based on Role ──────────────────────────────────────
function cm_apply_visibility(frm) {
	const isManager = cm_is_manager();
	const grid = frm.fields_dict.plans && frm.fields_dict.plans.grid;

	if (grid) {
		// actual_amount and price_gap: managers only
		grid.set_column_disp("actual_amount", isManager);
		grid.set_column_disp("price_gap",     isManager);
		// sale_amount always visible
		grid.set_column_disp("sale_amount",   true);
		frm.refresh_field("plans");
	}

	// Hide actual totals from sales
	frm.set_df_property("total_actual_amount", "hidden", !isManager);
	frm.set_df_property("total_price_gap",     "hidden", !isManager);

	// Sales person field: read-only for sales, editable for managers
	frm.set_df_property("sales_person", "read_only", !isManager);
}

// ── Workflow Buttons Setup ─────────────────────────────────────────────────────
function cm_setup_workflow_buttons(frm) {
	if (frm.is_new()) return;

	const state     = frm.doc.workflow_state;
	const isManager = cm_is_manager();
	const isSales   = frappe.user.has_role("Channel Sales");

	// Remove default workflow buttons and re-add styled ones
	frm.page.clear_secondary_action();

	if (state === "Draft" && isSales) {
		frm.add_custom_button(__("Submit for Approval"), () => {
			cm_apply_workflow_action(frm, "Submit for Approval");
		}).addClass("btn-primary");
	}

	if (state === "Pending Approval" && isManager) {
		frm.add_custom_button(__("Approve"), () => {
			cm_apply_workflow_action(frm, "Approve");
		}).addClass("btn-success");

		frm.add_custom_button(__("Reject"), () => {
			frappe.prompt(
				[{fieldname: "reason", fieldtype: "Text", label: "Rejection Reason", reqd: 1}],
				(values) => cm_apply_workflow_action(frm, "Reject", values.reason),
				__("Reason for Rejection"),
				__("Reject")
			);
		}).addClass("btn-danger");
	}

	if (state === "Rejected" && isSales) {
		frm.add_custom_button(__("Resubmit"), () => {
			cm_apply_workflow_action(frm, "Resubmit");
		}).addClass("btn-warning");
	}
}

function cm_apply_workflow_action(frm, action, reason) {
	frappe.confirm(
		__("Are you sure you want to {0}?", [action]),
		() => {
			frappe.call({
				method: "frappe.model.workflow.apply_workflow",
				args: {
					doc: frm.doc,
					action: action,
				},
				callback(r) {
					if (r.message) {
						frappe.model.sync(r.message);
						frm.refresh();
						frappe.show_alert({
							message: __("{0} action applied successfully.", [action]),
							indicator: "green"
						});
					}
				}
			});
		}
	);
}

// ── Custom Buttons ─────────────────────────────────────────────────────────────
function cm_add_custom_buttons(frm) {
	if (frm.is_new()) return;

	if (frm.doc.customer) {
		frm.add_custom_button(__("Customer Plans"), () => {
			frappe.set_route("List", "Customer Plan", { customer: frm.doc.customer });
		}, __("View"));
	}

	if (cm_is_manager()) {
		frm.add_custom_button(__("Sales Margin Report"), () => {
			frappe.set_route("query-report", "Sales Margin Report");
		}, __("View"));
	}
}
