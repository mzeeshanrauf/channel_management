// ─── Channel Management App JS ─────────────────────────────────────────────
// Injected on every page load via app_include_js

frappe.after_ajax(function () {
    injectRoleBodyClasses();
    applyFieldLevelSecurity();
});

/**
 * Add role classes to <body> so CSS can hide fields for non-managers.
 * Server-side permissions are the real guard; this is UX polish only.
 */
function injectRoleBodyClasses() {
    const roles = frappe.user_roles || [];
    if (roles.includes("Channel Manager") || roles.includes("Administrator")) {
        document.body.classList.add("has-role-channel-manager");
    }
    if (roles.includes("Channel Sales")) {
        document.body.classList.add("has-role-channel-sales");
    }
}

/**
 * On Sales Order form: hide actual price / price_gap columns
 * for Channel Sales users (server already prevents saving wrong values).
 */
function applyFieldLevelSecurity() {
    const isManager = frappe.user.has_role("Channel Manager") || frappe.user.has_role("Administrator");
    if (isManager) return;

    // Hook into form rendering
    $(document).on("form-refresh", function (e, frm) {
        if (!frm || frm.doctype !== "Sales Order") return;
        hideSensitiveSalesOrderColumns(frm);
    });
}

function hideSensitiveSalesOrderColumns(frm) {
    // Hide price_gap and actual rate columns in items child table
    const sensitiveFields = ["price_gap", "rate", "amount"];
    sensitiveFields.forEach(function (fieldname) {
        frm.fields_dict.items && frm.fields_dict.items.grid &&
            frm.fields_dict.items.grid.set_column_disp(fieldname, false);
    });

    // Hide the actual_rate_snapshot field if visible
    if (frm.fields_dict["total_discloseable_amount"]) {
        // Managers see grand total; sales see discloseable total
        // Replace the displayed grand_total label for sales
    }
}
