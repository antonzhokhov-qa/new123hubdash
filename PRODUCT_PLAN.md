# PSP Dashboard - Product Plan

## Overview

Универсальный дашборд для PSP команды (финансисты, сейлзы, операционщики) для мониторинга платежных транзакций, сверки данных между провайдерами и аналитики.

### Ключевые возможности

- **Multi-source aggregation** - сбор данных из Vima API и PayShack в единую БД
- **Real-time monitoring** - WebSocket обновления, near real-time синхронизация
- **Auto-reconciliation** - автоматическая сверка транзакций между источниками
- **Analytics & Metrics** - KPI, тренды, распределение по проектам/статусам
- **Export** - выгрузка в CSV/Excel для отчетности

---

## Current Status (v1.0)

### Implementation Progress

| Component | Status | Progress |
|-----------|--------|----------|
| **Backend** | Production Ready | 90% |
| **Frontend** | Production Ready | 85% |
| **Documentation** | Complete | 100% |
| **Testing** | Basic Coverage | 70% |

### Backend Components

| Module | Status | Description |
|--------|--------|-------------|
| API Routes | DONE | transactions, metrics, sync, reconciliation, export |
| WebSocket | DONE | Real-time updates broadcast |
| ETL Pipeline | DONE | Vima sync every 60s |
| Vima Integration | DONE | Client, normalizer, cursor-based loading |
| PayShack Integration | PARTIAL | Sync file ready, needs Playwright |
| Models | DONE | Transaction, SyncState, Reconciliation |
| Schemas | DONE | Pydantic validation |
| Services | DONE | ReconciliationService |
| Migrations | DONE | Initial schema |
| Tests | DONE | API, Vima client tests |

### Frontend Components

| Module | Status | Description |
|--------|--------|-------------|
| Layout | DONE | Header, Sidebar navigation |
| Dashboard | DONE | KPI cards, charts, recent transactions |
| Transactions | DONE | Table with filters, pagination |
| Reconciliation | DONE | Summary, discrepancies view |
| Sync Status | DONE | Source status cards |
| Charts | DONE | Trend, Donut, Bar charts (Recharts) |
| UI Components | DONE | shadcn/ui based |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SOURCES                                │
├──────────────────────────────────┬──────────────────────────────────────────┤
│         VIMA API                 │           PAYSHACK API                   │
│  payment.woozuki.com             │      api.payshack.in                     │
│  (REST, JSON, Cursor-based)      │  (Browser automation required)           │
└──────────────────────────────────┴──────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ETL PIPELINE                                    │
│                     APScheduler (60s Vima, 300s PayShack)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Fetcher → Normalizer → Deduplicator → Upsert → WebSocket Broadcast         │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE                                         │
├───────────────────────────────────┬─────────────────────────────────────────┤
│         PostgreSQL                │              Redis                       │
│    (Transactions, Reconciliation) │         (Cache, Sessions)               │
└───────────────────────────────────┴─────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  REST API: /transactions, /metrics, /reconciliation, /sync, /export         │
│  WebSocket: /ws/updates                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEXT.JS FRONTEND                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Dashboard │ Transactions │ Reconciliation │ Sync Status                    │
│  TanStack Query │ Zustand │ Recharts │ Tailwind + shadcn/ui                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Stories

### Financiers
- [x] View total volume by period with currency breakdown
- [x] View reconciliation summary with discrepancies
- [x] Export transactions to Excel/CSV
- [ ] Scheduled daily/weekly reports

### Sales
- [x] View transaction volume by project/merchant
- [x] See conversion rates by project
- [x] Track trends over time
- [ ] Merchant-specific analytics pages

### Operations
- [x] Real-time transaction feed
- [x] Sync status monitoring
- [x] Failed transactions visibility
- [ ] Alert system for anomalies

---

## API Endpoints

### Transactions
```
GET  /api/v1/transactions
GET  /api/v1/transactions/{id}
```

### Metrics
```
GET  /api/v1/metrics/overview
GET  /api/v1/metrics/by-project
GET  /api/v1/metrics/trends
```

### Sync
```
GET  /api/v1/sync/status
POST /api/v1/sync/trigger
```

### Reconciliation
```
GET  /api/v1/reconciliation/summary
GET  /api/v1/reconciliation/discrepancies
POST /api/v1/reconciliation/run
```

### Export
```
GET  /api/v1/export/transactions?format=csv|xlsx
```

### WebSocket
```
WS   /ws/updates
```

---

## Data Sources

### Vima/Finmar Collector API

**Production:** `https://payment.woozuki.com/collector1/api/v1/operation`

**Key Features:**
- API Key authentication
- Cursor-based pagination (operation_create_id, operation_update_id)
- Date range filtering
- Project/status filtering

**Key Fields:**
- `operation_id` - internal ID
- `client_operation_id` - matching key with PayShack
- `complete_amount`, `complete_currency`
- `current_status`, `payment_status`

See [docs/VIMA_API.md](docs/VIMA_API.md) for full documentation.

### PayShack API (Reversed)

**Base URL:** `https://api.payshack.in/`

**Key Features:**
- Session-based authentication
- Encrypted responses (CryptoJS AES)
- Browser automation required

**Key Fields:**
- `Order ID` - matching key with Vima (client_operation_id)
- `Transaction ID`, `UTR`
- `Amount`, `Paid Amount`, `Status`

See [docs/PAYSHACK_API.md](docs/PAYSHACK_API.md) for full documentation.

---

## Reconciliation

### Matching Strategy

Primary key: `client_operation_id` (Vima) = `Order ID` (PayShack)

### Discrepancy Types

| Type | Description |
|------|-------------|
| `matched` | Full match |
| `discrepancy_amount` | Amount differs |
| `discrepancy_status` | Status differs |
| `missing_vima` | Not found in Vima |
| `missing_payshack` | Not found in PayShack |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL 15, Redis 7 |
| Frontend | Next.js 14, React 18, TypeScript |
| UI | Tailwind CSS, shadcn/ui |
| Charts | Recharts |
| State | TanStack Query, Zustand |
| Automation | Playwright (for PayShack) |

---

## Project Structure

```
123hubuniversal/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # REST endpoints
│   │   ├── db/                # Database connections
│   │   ├── etl/               # Sync pipeline
│   │   ├── integrations/      # External API clients
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── migrations/
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/               # Next.js pages
│       ├── components/        # React components
│       ├── hooks/             # Custom hooks
│       ├── lib/               # Utilities
│       └── stores/            # Zustand stores
└── docs/
    ├── VIMA_API.md
    ├── PAYSHACK_API.md
    ├── ARCHITECTURE.md
    ├── BACKEND_TASKS.md
    ├── FRONTEND_SPEC.md
    ├── FRONTEND_TASKS.md
    └── API_CONTRACTS.md
```

---

## Remaining Work (v1.0 completion)

### High Priority
- [ ] PayShack browser automation (Playwright integration)
- [ ] Full PayShack sync implementation

### Medium Priority
- [ ] ClickHouse for analytics (optional optimization)
- [ ] Increase test coverage

### Low Priority
- [ ] Transaction detail modal in frontend
- [ ] Advanced export options

---

## Future Roadmap

See [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) for detailed future plans:

- **V1.1** - Period comparison, hourly heatmap
- **V1.2** - Alert system
- **V1.3** - Role-based dashboards
- **V2.0** - Merchant analytics
- **V2.1** - Scheduled reports
- **V3.0** - ML anomaly detection
