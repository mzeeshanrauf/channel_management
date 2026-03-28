frappe.pages["customer-dashboard"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Customer Dashboard"),
        single_column: true,
    });

    // ── Customer selector ────────────────────────────────────────────────────
    let customerField = page.add_field({
        label: __("Select Customer"),
        fieldtype: "Link",
        options: "Customer",
        fieldname: "customer",
        change() {
            let customer = customerField.get_value();
            if (customer) loadDashboard(customer);
        },
    });

    let $root = $(`<div class="cm-dashboard" style="margin-top:20px;"></div>`).appendTo($(wrapper).find(".page-content"));

    // ── Load Dashboard ───────────────────────────────────────────────────────
    function loadDashboard(customer) {
        $root.html(`<div class="text-center py-5"><i class="fa fa-spinner fa-spin fa-2x text-muted"></i></div>`);

        frappe.call({
            method: "channel_management.page.customer_dashboard.customer_dashboard.get_customer_plan_summary",
            args: { customer },
            callback(r) {
                if (r.message) renderDashboard(r.message);
            },
            error() {
                $root.html(`<div class="alert alert-danger">${__("Failed to load customer data.")}</div>`);
            }
        });
    }

    // ── Render Dashboard ─────────────────────────────────────────────────────
    function renderDashboard(data) {
        let c   = data.customer || {};
        let plans = data.plans || [];

        // Status badge colours
        const statusColor = {
            "Active":           "success",
            "Expiring Soon":    "warning",
            "Renewal Required": "danger",
            "Expired":          "secondary",
        };
        const statusIcon = {
            "Active":           "✅",
            "Expiring Soon":    "🟠",
            "Renewal Required": "🔴",
            "Expired":          "⚫",
        };

        let html = `
        <!-- Customer Info Card -->
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="fa fa-user"></i> &nbsp;${frappe.utils.escape_html(c.customer_name || "—")}</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3"><b>${__("Type")}</b><br>${c.customer_type || "—"}</div>
                    <div class="col-md-3"><b>${__("Mobile")}</b><br>${c.mobile_no || "—"}</div>
                    <div class="col-md-3"><b>${__("Email")}</b><br>${c.email_id || "—"}</div>
                    <div class="col-md-3"><b>${__("Territory")}</b><br>${c.territory || "—"}</div>
                </div>
            </div>
        </div>

        <!-- Summary KPI Cards -->
        <div class="row mb-4">
            ${kpiCard(__("Total Plans"),             data.total,            "primary",  "fa-list")}
            ${kpiCard(__("Active"),                  data.active,           "success",  "fa-check-circle")}
            ${kpiCard(__("Expiring Soon"),           data.expiring_soon,    "warning",  "fa-clock-o")}
            ${kpiCard(__("Renewal Required"),        data.renewal_required, "danger",   "fa-exclamation-circle")}
            ${kpiCard(__("Expired"),                 data.expired,          "secondary","fa-times-circle")}
        </div>

        <!-- Plans Table -->
        <div class="card shadow-sm">
            <div class="card-header">
                <h5 class="mb-0"><i class="fa fa-th-list"></i> &nbsp;${__("Plan Details")}</h5>
            </div>
            <div class="card-body p-0">
                ${plans.length === 0
                    ? `<div class="p-4 text-muted text-center">${__("No plans found for this customer.")}</div>`
                    : `<div class="table-responsive">
                        <table class="table table-hover table-bordered mb-0">
                            <thead class="thead-light">
                                <tr>
                                    <th>${__("Plan")}</th>
                                    <th>${__("Category")}</th>
                                    <th>${__("Start Date")}</th>
                                    <th>${__("End Date")}</th>
                                    <th>${__("Days Left")}</th>
                                    <th>${__("Status")}</th>
                                    <th>${__("Sales Order")}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${plans.map(p => `
                                <tr>
                                    <td><a href="/app/plan-master/${encodeURIComponent(p.plan)}">${frappe.utils.escape_html(p.plan)}</a></td>
                                    <td>${p.plan_category || "—"}</td>
                                    <td>${frappe.datetime.str_to_user(p.start_date) || "—"}</td>
                                    <td>${frappe.datetime.str_to_user(p.end_date) || "—"}</td>
                                    <td class="${p.days_to_expiry <= 7 ? 'text-danger font-weight-bold' : p.days_to_expiry <= 30 ? 'text-warning' : ''}">
                                        ${p.days_to_expiry != null ? p.days_to_expiry : "—"}
                                    </td>
                                    <td>
                                        <span class="badge badge-${statusColor[p.status] || 'secondary'}">
                                            ${statusIcon[p.status] || ""} ${__(p.status)}
                                        </span>
                                    </td>
                                    <td>${p.sales_order
                                        ? `<a href="/app/sales-order/${encodeURIComponent(p.sales_order)}">${frappe.utils.escape_html(p.sales_order)}</a>`
                                        : "—"}</td>
                                </tr>`).join("")}
                            </tbody>
                        </table>
                    </div>`
                }
            </div>
        </div>`;

        $root.html(html);
    }

    function kpiCard(label, value, color, icon) {
        return `
        <div class="col">
            <div class="card text-center border-${color} shadow-sm h-100">
                <div class="card-body">
                    <i class="fa ${icon} fa-2x text-${color} mb-2"></i>
                    <h2 class="text-${color} mb-0">${value || 0}</h2>
                    <p class="text-muted mb-0">${label}</p>
                </div>
            </div>
        </div>`;
    }
};
