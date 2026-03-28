# Channel Management — ERPNext v16 App

> DU Channel Partner SME Plan Management with Dual Pricing, KPI Tracking, and Renewal Alerts.

---

## 📦 Installation

### Prerequisites
- ERPNext v16 / Frappe v16
- Bench CLI installed

### Steps

```bash
# 1. Get the app
bench get-app channel_management /path/to/channel_management
# OR from git:
# bench get-app channel_management https://github.com/your-org/channel_management.git

# 2. Install on your site
bench --site your-site.local install-app channel_management

# 3. Run migrate to create DocTypes and custom fields
bench --site your-site.local migrate

# 4. Build assets
bench build --app channel_management

# 5. Restart bench
bench restart
```

---

## 🏗 Architecture Overview

```
channel_management/
├── doctype/
│   ├── plan_master/          ← SME Plan definitions
│   ├── channel_pricing/      ← Dual pricing (actual + discloseable)
│   ├── customer_plan/        ← Plan lifecycle tracker
│   └── kpi_target/           ← Employee KPI targets
│
├── events/
│   └── sales_order.py        ← Auto-fetch pricing on validate, create plan on submit
│
├── tasks/
│   └── daily.py              ← Scheduled: update plan statuses + KPI achievements
│
├── permissions/
│   ├── customer_plan.py      ← Sales see only own plans
│   └── kpi_target.py         ← Sales see only own KPIs
│
├── report/
│   ├── kpi_report/           ← Target vs Achieved (all roles)
│   ├── sales_margin_report/  ← Actual vs Discloseable (managers only)
│   └── renewal_report/       ← Expiring / renewal plans (all roles)
│
├── page/
│   └── customer_dashboard/   ← Per-customer plan summary page
│
├── api.py                    ← Whitelisted API endpoints
├── install.py                ← Roles + custom fields setup
└── hooks.py                  ← App entry point
```

---

## 👤 Roles

| Role              | Description                              |
|-------------------|------------------------------------------|
| `Channel Sales`   | Sales team — sees own data, discloseable prices only |
| `Channel Manager` | Management — full access, both prices, all reports   |

### Assign roles via:
> ERPNext → Settings → Users → [User] → Roles

---

## 📋 DocTypes

### Plan Master
Define SME plans. Each plan links to an ERPNext **Item** and has a validity period (Days / Months / Years).

### Channel Pricing
Stores the **dual price** per plan:
- **Actual Price** — real price (management only)
- **Discloseable Price** — reduced price shown to sales team
- Optional: Partner-specific pricing
- Optional: Effective date / expiry date

### Customer Plan
Auto-created when a Sales Order is submitted. Tracks:
- Customer → Plan → Sales Order linkage
- Start Date / End Date
- Status: `Active` → `Expiring Soon` → `Renewal Required` → `Expired`
- Pricing snapshot at time of sale

### KPI Target
Set per Sales Person per period (Monthly / Quarterly / Yearly):
- **Revenue** — sum of discloseable amounts
- **Sales Count** — number of orders
- **Renewals** — number of renewed plans
- Achieved value is **auto-calculated daily**

---

## 🔄 Core Flows

### Sales Flow
```
1. Sales creates Sales Order
2. Add item → set Plan field on item row
3. System auto-fetches Channel Pricing:
   - rate = actual_price (real Sales Order value)
   - discloseable_rate = reduced price (what sales sees)
   - price_gap = actual - discloseable
4. Submit Sales Order → Customer Plan created automatically
```

### Renewal Flow
```
Daily Scheduled Job runs:
- Plans with > 30 days left    → Active
- Plans with ≤ 30 days left    → Expiring Soon
- Plans with ≤ 7 days left     → Renewal Required
- Plans with 0 / past end date → Expired
```

### KPI Flow
```
Daily Scheduled Job runs:
- Sums discloseable_amount from submitted Sales Orders per sales person
- Updates KPI Target.achieved_value
- Calculates achievement % and sets status:
  ≥ 100% → Achieved
  ≥ 70%  → On Track
  ≥ 40%  → At Risk
  < 40%  → Missed
```

---

## 📊 Reports

### KPI Report
- Accessible by: Channel Sales (own only), Channel Manager (all)
- Filters: Sales Person, KPI Type, Period Type, Date Range
- Chart: Bar chart — Target vs Achieved per person

### Sales Margin Report
- Accessible by: **Channel Manager only**
- Shows: Actual Amount, Discloseable Amount, Price Gap, Margin %
- Summary cards: Total revenue, total gap, average margin
- Chart: Grouped bar per Sales Order

### Renewal Report
- Accessible by: Channel Sales (own), Channel Manager (all)
- Default view: Expiring Soon + Renewal Required + Expired
- Chart: Donut by status
- Summary: Count by status

---

## 📄 Customer Dashboard

Access via: **Channel Management → Customer Dashboard**

Select a customer to see:
- Customer info card (name, mobile, email, territory)
- KPI summary cards: Total / Active / Expiring Soon / Renewal Required / Expired
- Full plan table with status badges and Sales Order links

---

## 🔒 Security Model

| Feature                       | Channel Sales | Channel Manager |
|-------------------------------|:---:|:---:|
| See own Sales Orders          | ✅  | ✅  |
| See all Sales Orders          | ❌  | ✅  |
| See actual_price              | ❌  | ✅  |
| See discloseable_price        | ✅  | ✅  |
| See price_gap                 | ❌  | ✅  |
| Export Sales Margin Report    | ❌  | ✅  |
| Create/Edit Channel Pricing   | ❌  | ✅  |
| Create/Edit KPI Targets       | ❌  | ✅  |
| See own KPI                   | ✅  | ✅  |
| See all KPIs                  | ❌  | ✅  |
| Access Customer Dashboard     | ✅ (own) | ✅ (all) |

Security is enforced at **three levels**:
1. **DocType permissions** (JSON + install.py)
2. **has_permission hooks** (Python — per-document row-level)
3. **Report role restrictions** (JSON + Python validation)

CSS/JS field hiding is an additional UX layer only — not relied upon for security.

---

## ⚙️ Configuration After Install

1. **Create Plans** → Plan Master → New
2. **Set Pricing** → Channel Pricing → New (set both actual + discloseable prices)
3. **Assign Roles** → Users → add `Channel Sales` or `Channel Manager`
4. **Link Sales Person to User** → Sales Person → set `User ID` field
5. **Set KPI Targets** → KPI Target → New (set period, target value)
6. **Start selling** → Sales Order → add Item + Plan → submit

---

## 🔧 Scheduled Jobs

Both jobs run **daily at midnight** automatically:

| Job | Function |
|-----|----------|
| Update Plan Statuses | `channel_management.tasks.daily.update_plan_statuses` |
| Update KPI Achievements | `channel_management.tasks.daily.update_kpi_achievements` |

Run manually:
```bash
bench --site your-site.local execute channel_management.tasks.daily.update_plan_statuses
bench --site your-site.local execute channel_management.tasks.daily.update_kpi_achievements
```

---

## 🚀 Future Enhancements (Planned)
- Commission module per sales person
- Approval workflow for discount overrides
- CRM integration
- Mobile push alerts for renewal reminders
- ErpTronix mobile app integration

---

## 📝 License
MIT — ErpTronix
