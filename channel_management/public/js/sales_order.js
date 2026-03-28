// ─── Channel Management: Sales Order Client Script ───────────────────────────

function cm_is_manager() {
	return frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator");
}

frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		cm_apply_visibility(frm);
		cm_add_buttons(frm);
	},
	channel_partner(frm) {
		(frm.doc.items || []).forEach(row => {
			if (row.plan) cm_fetch_pricing(frm, row);
		});
		frm.refresh_field("items");
	},
});

frappe.ui.form.on("Sales Order Item", {
	plan(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.plan) {
			cm_fetch_pricing(frm, row, cdt, cdn);
		} else {
			frappe.model.set_value(cdt, cdn, { discloseable_rate: 0, discloseable_amount: 0, price_gap: 0 });
		}
	},
	qty(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.discloseable_rate) {
			frappe.model.set_value(cdt, cdn, "discloseable_amount", flt(row.discloseable_rate) * flt(row.qty));
			frappe.model.set_value(cdt, cdn, "price_gap", (flt(row.rate) - flt(row.discloseable_rate)) * flt(row.qty));
			cm_update_header_total(frm);
		}
	},
});

function cm_fetch_pricing(frm, row, cdt, cdn) {
	frappe.call({
		method: "channel_management.api.get_pricing_for_plan",
		args: { plan: row.plan, partner: frm.doc.channel_partner || null },
		callback(r) {
			if (!r.message) {
				frappe.msgprint({ message: __("No active Channel Pricing for plan: {0}", [row.plan]), indicator: "orange" });
				return;
			}
			const p   = r.message;
			const qty = flt(row.qty) || 1;
			const _cdt = cdt || row.doctype;
			const _cdn = cdn || row.name;

			frappe.model.set_value(_cdt, _cdn, "discloseable_rate",   p.discloseable_price);
			frappe.model.set_value(_cdt, _cdn, "discloseable_amount",  flt(p.discloseable_price) * qty);

			if (p.actual_price !== undefined) {
				frappe.model.set_value(_cdt, _cdn, "rate",      p.actual_price);
				frappe.model.set_value(_cdt, _cdn, "amount",    flt(p.actual_price) * qty);
				frappe.model.set_value(_cdt, _cdn, "price_gap", flt(p.price_gap) * qty);
			}
			cm_update_header_total(frm);
		},
	});
}

function cm_update_header_total(frm) {
	const total = (frm.doc.items || []).reduce((s, i) => s + flt(i.discloseable_amount), 0);
	frm.set_value("total_discloseable_amount", total);
}

function cm_apply_visibility(frm) {
	const isManager = cm_is_manager();
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid) return;
	grid.set_column_disp("price_gap", isManager);
	grid.set_column_disp("rate",      isManager);
	grid.set_column_disp("amount",    isManager);
	grid.set_column_disp("discloseable_rate",   true);
	grid.set_column_disp("discloseable_amount",  true);
	frm.refresh_field("items");
}

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
