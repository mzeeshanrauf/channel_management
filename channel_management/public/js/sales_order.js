// ─── Channel Management: Sales Order Client Script ───────────────────────────

function cm_is_manager() {
	return frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator");
}

// ── Issue 1 fix: auto-fetch Sales Person from logged-in user on form load ────
frappe.ui.form.on("Sales Order", {

	setup(frm) {
		// When a new SO is created, auto-add the logged-in user's sales person
		if (frm.is_new()) {
			cm_auto_set_sales_person(frm);
		}
	},

	refresh(frm) {
		// Re-apply on every refresh (new doc too)
		if (frm.is_new()) {
			cm_auto_set_sales_person(frm);
		}
		cm_apply_visibility(frm);
		cm_add_buttons(frm);
	},

	onload(frm) {
		if (frm.is_new()) {
			cm_auto_set_sales_person(frm);
		}
	},

	channel_partner(frm) {
		(frm.doc.items || []).forEach(row => {
			if (row.plan) cm_fetch_pricing(frm, row);
		});
		frm.refresh_field("items");
	},
});

// ── Issue 1 fix: pricing fetch on plan selection ──────────────────────────────
frappe.ui.form.on("Sales Order Item", {

	// Fix: use item_code trigger too in case plan is set alongside item
	plan(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.plan) {
			cm_fetch_pricing(frm, row, cdt, cdn);
		} else {
			frappe.model.set_value(cdt, cdn, "discloseable_rate", 0);
			frappe.model.set_value(cdt, cdn, "discloseable_amount", 0);
			frappe.model.set_value(cdt, cdn, "price_gap", 0);
		}
	},

	qty(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.discloseable_rate) {
			frappe.model.set_value(cdt, cdn, "discloseable_amount",
				flt(row.discloseable_rate) * flt(row.qty));
			frappe.model.set_value(cdt, cdn, "price_gap",
				(flt(row.rate) - flt(row.discloseable_rate)) * flt(row.qty));
			cm_update_header_total(frm);
		}
	},
});

// ── Fix Issue 1: Pricing fetch — uses frappe.call with proper error handling ──
function cm_fetch_pricing(frm, row, cdt, cdn) {
	if (!row.plan) return;

	// Resolve cdt/cdn if not passed directly
	const _cdt = cdt || row.doctype;
	const _cdn = cdn || row.name;

	frappe.call({
		method: "channel_management.api.get_pricing_for_plan",
		args: {
			plan: row.plan,
			partner: frm.doc.channel_partner || null
		},
		freeze: false,
		callback(r) {
			if (!r || !r.message) {
				frappe.show_alert({
					message: __("No active Channel Pricing found for plan: {0}", [row.plan]),
					indicator: "orange"
				});
				return;
			}

			const p   = r.message;
			const qty = flt(row.qty) || 1;

			// Always set discloseable fields (visible to all)
			frappe.model.set_value(_cdt, _cdn, "discloseable_rate",  flt(p.discloseable_price));
			frappe.model.set_value(_cdt, _cdn, "discloseable_amount", flt(p.discloseable_price) * qty);

			// Set actual rate — returned for managers, also set for sales so SO totals work
			// Server-side the actual price is always used for the real SO value
			if (p.actual_price !== undefined && p.actual_price > 0) {
				frappe.model.set_value(_cdt, _cdn, "rate",      flt(p.actual_price));
				frappe.model.set_value(_cdt, _cdn, "amount",    flt(p.actual_price) * qty);
				frappe.model.set_value(_cdt, _cdn, "price_gap", flt(p.price_gap) * qty);
			} else {
				// For sales role: API only returns discloseable_price
				// Set rate = discloseable so SO totals are populated
				frappe.model.set_value(_cdt, _cdn, "rate",   flt(p.discloseable_price));
				frappe.model.set_value(_cdt, _cdn, "amount", flt(p.discloseable_price) * qty);
			}

			cm_update_header_total(frm);
			frm.refresh_field("items");
		},
		error() {
			frappe.show_alert({
				message: __("Error fetching pricing for plan: {0}", [row.plan]),
				indicator: "red"
			});
		}
	});
}

// ── Fix Issue 2: Auto-set Sales Person from logged-in user ───────────────────
function cm_auto_set_sales_person(frm) {
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "Sales Person",
			filters: { user_id: frappe.session.user },
			fieldname: "name"
		},
		callback(r) {
			if (!r.message || !r.message.name) return;

			const sp = r.message.name;

			// Check if already in sales_team
			const already = (frm.doc.sales_team || []).find(t => t.sales_person === sp);
			if (already) return;

			// Add to sales_team table
			const row = frm.add_child("sales_team");
			frappe.model.set_value(row.doctype, row.name, "sales_person", sp);
			frappe.model.set_value(row.doctype, row.name, "allocated_percentage", 100);
			frm.refresh_field("sales_team");
		}
	});
}

// ── Fix Issue 3: Field visibility based on role ───────────────────────────────
function cm_apply_visibility(frm) {
	const isManager = cm_is_manager();
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;

	if (grid) {
		// Managers see everything; sales see only discloseable columns
		grid.set_column_disp("rate",               isManager);
		grid.set_column_disp("amount",             isManager);
		grid.set_column_disp("price_gap",          isManager);
		grid.set_column_disp("discloseable_rate",  true);
		grid.set_column_disp("discloseable_amount", true);
		frm.refresh_field("items");
	}

	// Hide the actual grand total from sales; show discloseable total instead
	if (!isManager) {
		frm.set_df_property("grand_total",          "hidden", 1);
		frm.set_df_property("rounded_total",        "hidden", 1);
		frm.set_df_property("total_discloseable_amount", "hidden", 0);
	} else {
		frm.set_df_property("grand_total",          "hidden", 0);
		frm.set_df_property("rounded_total",        "hidden", 0);
		frm.set_df_property("total_discloseable_amount", "hidden", 0);
	}

	// Hide Channel Pricing section from sales (they don't need to see the gap total)
	frm.set_df_property("total_discloseable_amount", "label",
		isManager ? "Total Discloseable Amount" : "Your Sales Total");
}

// ── Recalculate header discloseable total ─────────────────────────────────────
function cm_update_header_total(frm) {
	const total = (frm.doc.items || []).reduce((s, i) => s + flt(i.discloseable_amount), 0);
	frm.set_value("total_discloseable_amount", total);
}

// ── Custom buttons ─────────────────────────────────────────────────────────────
function cm_add_buttons(frm) {
	if (!frm.doc.customer || frm.is_new()) return;

	frm.add_custom_button(__("Customer Plans"), () => {
		frappe.set_route("List", "Customer Plan", { customer: frm.doc.customer });
	}, __("Channel"));

	if (cm_is_manager()) {
		frm.add_custom_button(__("Sales Margin Report"), () => {
			frappe.set_route("query-report", "Sales Margin Report", { customer: frm.doc.customer });
		}, __("Channel"));
	}
}
