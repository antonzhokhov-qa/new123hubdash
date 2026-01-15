# PSP Dashboard - Feature Roadmap

## Overview

Roadmap будущих фич для PSP Dashboard, приоритизированный на основе анализа Reddit, fintech best practices и потребностей команды (финансисты, сейлзы, операционщики).

---

## Data Constraints

При планировании фич учитываем ограничения данных:

| Available | Not Available |
|-----------|---------------|
| Transactions (Vima + PayShack) | Chargebacks/Refunds details |
| Amount, status, timestamp | Decline reasons |
| Project/Merchant ID | Revenue share / commissions |
| User email/phone | User behavior / sessions |
| client_operation_id (c_id) | Settlements data |

---

## Roadmap

### V1.1 - Analytics Improvements (2-3 weeks)

**Target Users:** All roles

#### New Metrics
- [ ] Average ticket size by project
- [ ] Hourly distribution heatmap (when most transactions happen)
- [ ] Success rate trend (not just current, but dynamics)
- [ ] Top 5 / Bottom 5 merchants by conversion

#### New Filters
- [ ] By payment_method (apm, card, upi)
- [ ] By currency
- [ ] Multi-select for projects

#### Period Comparison
- [ ] Today vs Yesterday
- [ ] This week vs Last week
- [ ] Custom date range comparison

**Priority:** HIGH
**Effort:** LOW-MEDIUM

---

### V1.2 - Alert System (2-3 weeks)

**Target Users:** Operations, Management

#### Alert Rules Engine

```
Example rules:
- Success rate dropped below 80% in last hour
- No transactions from project X for 30+ minutes
- Sudden spike in failed transactions (>2x average)
- Anomalous transaction amount (>3 std from average)
```

#### Notification Channels
- [ ] In-dashboard (bell icon + badge)
- [ ] Email (optional)
- [ ] Telegram bot (optional)

#### UI Components
- [ ] Alert center (active alerts list)
- [ ] Alert history
- [ ] Alert configuration page

**Priority:** HIGH
**Effort:** MEDIUM

---

### V1.3 - Role-based Dashboards (2-3 weeks)

**Target Users:** All roles (customized views)

#### For Financiers
- [ ] Emphasis on reconciliation
- [ ] Summary by amounts and currencies
- [ ] Discrepancies highlight
- [ ] Export to Excel with pivot-ready format

#### For Sales
- [ ] Merchant performance cards
- [ ] Conversion trends by merchant
- [ ] Comparison between merchants
- [ ] "Health score" for each merchant

#### For Operations
- [ ] Real-time transaction feed
- [ ] System status (sync health)
- [ ] Failed transactions drill-down
- [ ] Quick filters for troubleshooting

**Priority:** MEDIUM
**Effort:** MEDIUM

---

### V2.0 - Extended Analytics (4-6 weeks)

**Target Users:** Sales, Management

#### Merchant Analytics Page

```
Route: /merchants/{id}/analytics

Features:
- Dedicated page per merchant
- Historical performance
- Daily/weekly/monthly reports
- Trend predictions (simple moving average)
```

#### Failure Analysis
- [ ] Group failed by original_status
- [ ] Pattern detection (e.g., all failed at specific time)
- [ ] Correlation with payment method

#### Cohort-like Analysis
- [ ] Transactions by day of week
- [ ] Transactions by hour of day
- [ ] Seasonal patterns

**Priority:** MEDIUM
**Effort:** HIGH

---

### V2.1 - Report Automation (2-3 weeks)

**Target Users:** Financiers, Management

#### Scheduled Reports
- [ ] Daily summary email
- [ ] Weekly reconciliation report
- [ ] Monthly merchant performance

#### Report Builder
- [ ] Select metrics
- [ ] Select period
- [ ] Select format (PDF, Excel, CSV)
- [ ] Schedule (daily/weekly/monthly)

**Priority:** MEDIUM
**Effort:** MEDIUM

---

### V3.0 - Advanced Features (6-8 weeks, future)

**Target Users:** Operations, Management

#### Anomaly Detection (ML-light)
- [ ] Z-score based anomaly detection
- [ ] Rolling averages + threshold alerts
- [ ] Pattern recognition (unusual transaction times/amounts)

#### Predictive Analytics
- [ ] Expected daily volume (based on history)
- [ ] Trend forecasting (simple linear regression)
- [ ] "What-if" scenarios

#### API for External Systems
- [ ] Webhook notifications
- [ ] REST API for integration with other systems
- [ ] Embeddable widgets

**Priority:** LOW
**Effort:** HIGH

---

## Prioritization Matrix

```
                    HIGH IMPACT
                         │
    Period Comparison ●  │  ● Alert System
                         │
    Hourly Heatmap ●     │     ● Role Dashboards
                         │
    ─────────────────────┼─────────────────────
    LOW EFFORT           │           HIGH EFFORT
                         │
    Merchant Page ●      │  ● Scheduled Reports
                         │
                         │     ● ML Anomaly
                         │
                    LOW IMPACT
```

---

## Recommended Implementation Order

| Priority | Feature | Reason |
|----------|---------|--------|
| 1 | Period comparison | Low effort, high impact for all roles |
| 2 | Alert system | Critical for operations, reduces response time |
| 3 | Hourly heatmap | Helps understand patterns, easy to implement |
| 4 | Role-based views | Each role sees what they need |
| 5 | Merchant analytics | Important for sales |
| 6 | Scheduled reports | Automates financiers' routine |
| 7 | Advanced ML | Only after stabilizing basic features |

---

## Technical Considerations

### Period Comparison
- Backend: Add `compare_from`, `compare_to` params to metrics endpoints
- Frontend: Add comparison toggle, show delta values in KPI cards

### Alert System
- Backend: New `alerts` table, background checker service
- Frontend: Bell icon in header, alert configuration page
- Optional: Celery tasks for email/telegram notifications

### Role-based Views
- Backend: User roles in session/JWT, filtered responses
- Frontend: Conditional rendering based on role

### Hourly Heatmap
- Backend: New endpoint `/metrics/hourly-distribution`
- Frontend: Heatmap component (7 days x 24 hours grid)

---

## Research Sources

Based on analysis from:
- Reddit r/fintech, r/SaaS, r/ProductManagement
- Fintech dashboard best practices
- PSP industry standards

### Key Insights from Research

1. **Alerts and anomaly detection** - Users want to know not just "what" happened but "why" the metric changed
2. **Role-based views** - Different dashboards for different roles
3. **Drill-down and interactivity** - Ability to "dive into" details
4. **Period comparison** - Current vs previous (day/week/month)
5. **Minimalism** - Fewer metrics, but the most important ones
6. **Real-time or near real-time** updates
