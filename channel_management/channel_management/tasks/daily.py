import frappe
from frappe.utils import today, getdate, date_diff
from channel_management.channel_management.channel_management.doctype.kpi_target.kpi_target import get_achieved_value


def update_plan_statuses():
    """Daily: update Customer Plan statuses based on expiry dates."""
    today_date = getdate(today())

    plans = frappe.get_all(
        "Customer Plan",
        filters={"status": ["not in", ["Cancelled", "Expired"]]},
        fields=["name", "end_date", "status"]
    )

    updated = 0
    for p in plans:
        if not p.end_date:
            continue

        days_left = date_diff(p.end_date, today_date)

        if days_left < 0:
            new_status = "Expired"
        elif days_left <= 7:
            new_status = "Renewal Required"
        elif days_left <= 30:
            new_status = "Expiring Soon"
        else:
            new_status = "Active"

        if new_status != p.status:
            frappe.db.set_value(
                "Customer Plan", p.name,
                {"status": new_status, "days_to_expiry": days_left},
                update_modified=False
            )
            updated += 1

    frappe.db.commit()
    frappe.logger().info(f"[Channel Management] Plan statuses updated: {updated}")


def update_kpi_achievements():
    """Daily: recalculate KPI achieved values for active periods."""
    today_date = getdate(today())

    kpis = frappe.get_all(
        "KPI Target",
        filters={
            "period_start": ["<=", today_date],
            "period_end":   [">=", today_date],
        },
        fields=["name", "sales_person", "kpi_type", "period_start", "period_end", "target_value"]
    )

    for k in kpis:
        achieved = get_achieved_value(
            k.sales_person, k.kpi_type, k.period_start, k.period_end
        )
        pct = (achieved / k.target_value * 100) if k.target_value else 0

        if pct >= 100:
            status = "Achieved"
        elif pct >= 70:
            status = "On Track"
        elif pct >= 40:
            status = "At Risk"
        else:
            status = "Missed"

        frappe.db.set_value(
            "KPI Target", k.name,
            {"achieved_value": achieved, "achievement_percentage": pct, "status": status},
            update_modified=False
        )

    frappe.db.commit()
    frappe.logger().info(f"[Channel Management] KPI achievements updated: {len(kpis)}")
