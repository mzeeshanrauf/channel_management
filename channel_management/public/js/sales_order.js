// ─── Channel Management: Sales Order Client Script ───────────────────────────
// Served via doctype_js hook — no esbuild bundle required.

// ── Role helpers ──────────────────────────────────────────────────────────────
function cm_is_manager() {
    return frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator");
}

// ── Sales Order form events ───────────────────────────────────────────────────
frappe.ui.form.on("Sales Order", {
    refresh: function (frm) {
        applyFieldVisibility(frm);
        addCustomButtons(frm);
    },
    channel_partner: function (frm) {
        (frm.doc.items || []).forEach(function (item) {
            if (item.plan) fetchAndSetPricing(frm, item);
        });
        frm.refresh_field("items");
    },
});

frappe.ui.form.on("Sales Order Item", {
    plan: function (frm, cdt, cdn) {
        let item = locals[cdt][cdn];
        if (item.plan) {
            fetchAndSetPricing(frm, item, cdt, cdn);
        } else {
            frappe.model.set_value(cdt, cdn, "discloseable_rate",   0);
            frappe.model.set_value(cdt, cdn, "discloseable_amount",  0);
            frappe.model.set_value(cdt, cdn, "price_gap",           0);
        }
    },
    qty: function (frm, cdt, cdn) {
        let item = locals[cdt][cdn];
        if (item.discloseable_rate) {
            frappe.model.set_value(cdt, cdn, "discloseable_amount",
                flt(item.discloseable_rate) * flt(item.qty));
            frappe.model.set_value(cdt, cdn, "price_gap",
                (flt(item.rate) - flt(item.discloseable_rate)) * flt(item.qty));
            updateHeaderTotal(frm);
        }
    },
});

function fetchAndSetPricing(frm, item, cdt, cdn) {
    frappe.call({
        method: "channel_management.api.get_pricing_for_plan",
        args:   { plan: item.plan, partner: frm.doc.channel_partner || null },
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint({ message: __("No active Channel Pricing found for plan: {0}", [item.plan]), indicator: "orange" });
                return;
            }
            let p   = r.message;
            let qty = flt(item.qty) || 1;
            let _cdt = cdt || item.doctype;
            let _cdn = cdn || item.name;

            frappe.model.set_value(_cdt, _cdn, "discloseable_rate",  p.discloseable_price);
            frappe.model.set_value(_cdt, _cdn, "discloseable_amount", flt(p.discloseable_price) * qty);

            if (p.actual_price !== undefined) {
                frappe.model.set_value(_cdt, _cdn, "rate",      p.actual_price);
                frappe.model.set_value(_cdt, _cdn, "amount",    flt(p.actual_price) * qty);
                frappe.model.set_value(_cdt, _cdn, "price_gap", flt(p.price_gap) * qty);
            }
            updateHeaderTotal(frm);
        }
    });
}

function updateHeaderTotal(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(function (i) { total += flt(i.discloseable_amount); });
    frm.set_value("total_discloseable_amount", total);
}

function applyFieldVisibility(frm) {
    let isManager = cm_is_manager();
    let grid = frm.fields_dict.items && frm.fields_dict.items.grid;
    if (!grid) return;
    grid.set_column_disp("price_gap", isManager);
    grid.set_column_disp("rate",      isManager);
    grid.set_column_disp("amount",    isManager);
    grid.set_column_disp("discloseable_rate",   true);
    grid.set_column_disp("discloseable_amount",  true);
    frm.refresh_field("items");
}

function addCustomButtons(frm) {
    if (!frm.doc.customer || frm.is_new()) return;
    frm.add_custom_button(__("Customer Plans"), function () {
        frappe.set_route("List", "Customer Plan", { customer: frm.doc.customer });
    }, __("Channel"));
    if (cm_is_manager()) {
        frm.add_custom_button(__("Sales Margin Report"), function () {
            frappe.set_route("query-report", "Sales Margin Report", { customer: frm.doc.customer });
        }, __("Channel"));
    }
}
