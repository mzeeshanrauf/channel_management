// Sales Order client-side customization for Channel Management
// Handles plan-based pricing auto-fetch and field visibility

frappe.ui.form.on("Sales Order", {
    refresh: function (frm) {
        applyFieldVisibility(frm);
        addCustomButtons(frm);
    },

    channel_partner: function (frm) {
        // Re-fetch pricing for all items when partner changes
        frm.doc.items.forEach(function (item) {
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
            // Clear channel fields
            frappe.model.set_value(cdt, cdn, "discloseable_rate",   0);
            frappe.model.set_value(cdt, cdn, "discloseable_amount",  0);
            frappe.model.set_value(cdt, cdn, "price_gap",           0);
        }
    },

    qty: function (frm, cdt, cdn) {
        let item = locals[cdt][cdn];
        if (item.discloseable_rate) {
            frappe.model.set_value(cdt, cdn, "discloseable_amount", item.discloseable_rate * item.qty);
            frappe.model.set_value(cdt, cdn, "price_gap",
                (item.rate - item.discloseable_rate) * item.qty);
            updateHeaderTotal(frm);
        }
    },
});

// ── Fetch pricing from Channel Pricing via API ────────────────────────────

function fetchAndSetPricing(frm, item, cdt, cdn) {
    let partner = frm.doc.channel_partner || null;

    frappe.call({
        method: "channel_management.api.get_pricing_for_plan",
        args: { plan: item.plan, partner: partner },
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint({
                    message: __("No active pricing found for plan: {0}", [item.plan]),
                    indicator: "orange",
                });
                return;
            }

            let pricing = r.message;
            let qty     = item.qty || 1;

            if (cdt && cdn) {
                frappe.model.set_value(cdt, cdn, "discloseable_rate",   pricing.discloseable_price);
                frappe.model.set_value(cdt, cdn, "discloseable_amount",  pricing.discloseable_price * qty);

                // actual_price and price_gap only set if manager (server returns them)
                if (pricing.actual_price !== undefined) {
                    frappe.model.set_value(cdt, cdn, "rate",      pricing.actual_price);
                    frappe.model.set_value(cdt, cdn, "amount",    pricing.actual_price * qty);
                    frappe.model.set_value(cdt, cdn, "price_gap", pricing.price_gap * qty);
                }
            }
            updateHeaderTotal(frm);
        }
    });
}

// ── Recalculate header discloseable total ────────────────────────────────

function updateHeaderTotal(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(function (item) {
        total += flt(item.discloseable_amount);
    });
    frm.set_value("total_discloseable_amount", total);
}

// ── Field visibility based on role ───────────────────────────────────────

function applyFieldVisibility(frm) {
    let isManager = frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator");

    // Column visibility in items grid
    frm.fields_dict.items && frm.fields_dict.items.grid &&
        frm.fields_dict.items.grid.set_column_disp("price_gap", isManager);

    // Show/hide channel pricing section
    frm.set_df_property("channel_section", "hidden", 0);
    frm.set_df_property("total_discloseable_amount", "hidden", 0);

    // For sales: hide rate (actual), show discloseable_amount only
    if (!isManager) {
        frm.fields_dict.items && frm.fields_dict.items.grid &&
            frm.fields_dict.items.grid.set_column_disp("rate", false);
        frm.fields_dict.items && frm.fields_dict.items.grid &&
            frm.fields_dict.items.grid.set_column_disp("amount", false);
    }

    frm.refresh_field("items");
}

// ── Custom Buttons ────────────────────────────────────────────────────────

function addCustomButtons(frm) {
    if (!frm.doc.customer || frm.is_new()) return;

    frm.add_custom_button(__("Customer Plans"), function () {
        frappe.set_route("List", "Customer Plan", { customer: frm.doc.customer });
    }, __("View"));

    if (frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator")) {
        frm.add_custom_button(__("Sales Margin Report"), function () {
            frappe.set_route("query-report", "Sales Margin Report", {
                customer: frm.doc.customer,
            });
        }, __("View"));
    }
}
