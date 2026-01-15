# PSP Dashboard Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SOURCES                                │
├──────────────────────────────────┬──────────────────────────────────────────┤
│         VIMA API                 │           PAYSHACK API                   │
│  payment.woozuki.com             │      api.payshack.in                     │
│  (REST, JSON, Open)              │  (REST, Encrypted, Browser Auth)         │
└──────────────────────────────────┴──────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA INGESTION                                  │
├──────────────────────────────────┬──────────────────────────────────────────┤
│       Vima Fetcher               │        PayShack Fetcher                  │
│  - HTTP Client                   │  - Playwright Browser                    │
│  - Cursor-based pagination       │  - DOM Scraping                          │
│  - Every 5 minutes               │  - Session management                    │
└──────────────────────────────────┴──────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NORMALIZERS                                     │
│  - Map source-specific fields to unified Transaction model                   │
│  - Status normalization                                                      │
│  - Amount/currency parsing                                                   │
│  - Timestamp conversion (UTC)                                                │
│  - Deduplication (hash-based)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                   │
├───────────────────┬─────────────────────────────┬───────────────────────────┤
│    PostgreSQL     │          Redis              │      ClickHouse           │
│  (Primary Store)  │        (Cache)              │    (Analytics)            │
│                   │                             │                           │
│  - transactions   │  - Hot metrics (1min TTL)   │  - hourly_metrics         │
│  - sync_state     │  - Session data             │  - daily_aggregates       │
│  - reconciliation │  - Rate limiting            │  - Fast aggregations      │
└───────────────────┴─────────────────────────────┴───────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API                                     │
│                           (FastAPI + Python)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  /api/v1/transactions    - List, filter, paginate                           │
│  /api/v1/metrics         - Overview, trends, by-project                     │
│  /api/v1/reconciliation  - Summary, discrepancies, run                      │
│  /api/v1/export          - CSV, Excel export                                │
│  /api/v1/sync            - Sync status, trigger                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                        (React + Next.js)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  - Dashboard with KPI cards                                                  │
│  - Transaction tables with filters                                           │
│  - Charts (ECharts/Recharts)                                                 │
│  - Reconciliation reports                                                    │
│  - Export functionality                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### PostgreSQL - Main Tables

#### transactions
```sql
CREATE TABLE transactions (
    -- Primary Key
    id UUID DEFAULT gen_random_uuid(),
    
    -- Source identification
    source VARCHAR(20) NOT NULL,              -- 'vima' | 'payshack'
    source_id VARCHAR(255) NOT NULL,          -- Original ID from source
    
    -- Matching keys
    reference_id VARCHAR(255),                -- Vima reference_id
    client_operation_id VARCHAR(255),         -- c_id (KEY FOR MATCHING!)
    order_id VARCHAR(255),                    -- PayShack order_id
    
    -- Business data
    project VARCHAR(100),                     -- monetix, caroussel, 91game
    merchant_id VARCHAR(255),
    
    -- Financial
    amount DECIMAL(18,4) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    fee DECIMAL(18,4),
    
    -- Status
    status VARCHAR(30) NOT NULL,              -- success | failed | pending
    original_status VARCHAR(50),              -- Original from source
    
    -- Payer info
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    user_phone VARCHAR(50),
    user_name VARCHAR(255),
    country CHAR(2),
    
    -- UTR (PayShack specific)
    utr VARCHAR(100),
    
    -- Payment method
    payment_method VARCHAR(50),
    payment_product VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Cursors (Vima specific)
    source_create_cursor VARCHAR(100),
    source_update_cursor VARCHAR(100),
    
    -- Raw data storage
    raw_data JSONB,
    
    -- Deduplication
    data_hash VARCHAR(64),
    
    -- System timestamps
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Partitioning key
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE transactions_2026_01 PARTITION OF transactions
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Indexes
CREATE INDEX idx_txn_source_date ON transactions (source, created_at DESC);
CREATE INDEX idx_txn_project ON transactions (project, created_at DESC);
CREATE INDEX idx_txn_status ON transactions (status, created_at DESC);
CREATE INDEX idx_txn_client_op_id ON transactions (client_operation_id);
CREATE INDEX idx_txn_order_id ON transactions (order_id);
CREATE INDEX idx_txn_data_hash ON transactions (data_hash);
CREATE UNIQUE INDEX idx_txn_source_source_id ON transactions (source, source_id, created_at);
```

#### sync_state
```sql
CREATE TABLE sync_state (
    id SERIAL PRIMARY KEY,
    source VARCHAR(20) NOT NULL UNIQUE,
    
    -- Cursors
    last_create_cursor VARCHAR(100),
    last_update_cursor VARCHAR(100),
    
    -- Timestamps
    last_sync_at TIMESTAMPTZ,
    last_successful_sync TIMESTAMPTZ,
    
    -- Status
    sync_status VARCHAR(20) DEFAULT 'idle',   -- idle | running | failed
    error_message TEXT,
    records_synced INT DEFAULT 0,
    
    -- Metadata
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initialize
INSERT INTO sync_state (source) VALUES ('vima'), ('payshack');
```

#### reconciliation_results
```sql
CREATE TABLE reconciliation_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Run info
    recon_date DATE NOT NULL,
    recon_run_id UUID NOT NULL,
    run_started_at TIMESTAMPTZ,
    run_completed_at TIMESTAMPTZ,
    
    -- Transaction references
    vima_txn_id UUID,
    payshack_txn_id UUID,
    client_operation_id VARCHAR(255),
    
    -- Match result
    match_status VARCHAR(30) NOT NULL,        -- matched | discrepancy | missing_vima | missing_payshack
    
    -- Discrepancy details
    discrepancy_type VARCHAR(50),             -- amount | status | time | missing
    
    -- Values comparison
    vima_amount DECIMAL(18,4),
    payshack_amount DECIMAL(18,4),
    amount_diff DECIMAL(18,4),
    
    vima_status VARCHAR(30),
    payshack_status VARCHAR(30),
    
    -- Additional details
    details JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recon_date ON reconciliation_results (recon_date, match_status);
CREATE INDEX idx_recon_run ON reconciliation_results (recon_run_id);
CREATE INDEX idx_recon_client_op ON reconciliation_results (client_operation_id);
```

---

## ETL Pipeline

### Vima Sync Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Scheduler  │────▶│  Get Cursor  │────▶│  Fetch API  │────▶│  Normalize   │
│  (5 min)    │     │  from DB     │     │  with cursor│     │  Transform   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Update     │◀────│  Update      │◀────│  Dedupe     │◀────│  Validate    │
│  Cursor     │     │  Sync State  │     │  by Hash    │     │  Data        │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

### PayShack Sync Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Scheduler  │────▶│  Check       │────▶│  Start      │────▶│  Navigate    │
│  (10 min)   │     │  Session     │     │  Browser    │     │  to Page     │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Update     │◀────│  Normalize   │◀────│  Parse      │◀────│  Wait for    │
│  DB         │     │  Data        │     │  DOM        │     │  Data Load   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

---

## Reconciliation Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         START RECONCILIATION                                 │
│                         (for date: YYYY-MM-DD)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Load all Vima transactions for date (where project in ['91game'])       │
│  2. Load all PayShack transactions for date                                  │
│  3. Build index by client_operation_id / order_id                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FOR EACH Vima transaction:                                                  │
│    - Find matching PayShack by client_operation_id                          │
│    - If found: compare amount, status, time                                  │
│    - If not found: mark as MISSING_PAYSHACK                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FOR EACH unmatched PayShack transaction:                                    │
│    - Mark as MISSING_VIMA                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Save results to reconciliation_results table                                │
│  Generate summary report                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REDIS CACHE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Key Pattern                          │ TTL     │ Description               │
│  ─────────────────────────────────────┼─────────┼─────────────────────────  │
│  metrics:overview:{params_hash}       │ 60s     │ Dashboard overview        │
│  metrics:trends:{params_hash}         │ 300s    │ Trend charts              │
│  metrics:by_project:{params_hash}     │ 300s    │ Per-project metrics       │
│  sync:status                          │ 30s     │ Sync status               │
│  recon:summary:{date}                 │ 3600s   │ Daily reconciliation      │
│  session:payshack                     │ 1800s   │ PayShack browser session  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
psp-dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── transactions.py
│   │   │   │   ├── metrics.py
│   │   │   │   ├── reconciliation.py
│   │   │   │   ├── export.py
│   │   │   │   └── sync.py
│   │   │   └── deps.py             # Dependencies
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── transaction.py
│   │   │   ├── sync_state.py
│   │   │   └── reconciliation.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── transaction.py
│   │   │   ├── metrics.py
│   │   │   └── reconciliation.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transaction_service.py
│   │   │   ├── metrics_service.py
│   │   │   └── reconciliation_service.py
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── vima/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py
│   │   │   │   └── normalizer.py
│   │   │   └── payshack/
│   │   │       ├── __init__.py
│   │   │       ├── client.py
│   │   │       └── normalizer.py
│   │   ├── etl/
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py
│   │   │   ├── vima_sync.py
│   │   │   └── payshack_sync.py
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── session.py
│   │       └── redis.py
│   ├── migrations/
│   │   └── versions/
│   ├── tests/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                        # (Separate repo/folder)
├── docker-compose.yml
├── .env.example
└── docs/
    ├── VIMA_API.md
    ├── PAYSHACK_API.md
    ├── ARCHITECTURE.md
    └── BACKEND_TASKS.md
```

---

## Technology Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| **Backend** | Python 3.11 + FastAPI | Async, typed, fast development |
| **Database** | PostgreSQL 15 | ACID, partitioning, JSONB |
| **Cache** | Redis 7 | Fast, TTL support |
| **Analytics** | ClickHouse (optional) | Fast aggregations |
| **Task Queue** | APScheduler / Celery | Background jobs |
| **Browser Automation** | Playwright | PayShack scraping |
| **ORM** | SQLAlchemy 2.0 | Async support |
| **Migrations** | Alembic | Version control |
| **Frontend** | React + Next.js | SSR, TypeScript |
| **Charts** | ECharts / Recharts | Performance |
| **UI** | Tailwind + shadcn/ui | Modern design |

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/psp_dashboard
REDIS_URL=redis://localhost:6379/0

# Vima API
VIMA_API_KEY=master-3E193252DE4A4B4C80862F67B2972D3D
VIMA_BASE_URL=https://payment.woozuki.com/collector1/api/v1

# PayShack
PAYSHACK_EMAIL=psrs1@gmail.com
PAYSHACK_PASSWORD=Payshacksub@123
PAYSHACK_BASE_URL=https://dashboard.payshack.in

# Sync settings
VIMA_SYNC_INTERVAL_MINUTES=5
PAYSHACK_SYNC_INTERVAL_MINUTES=10

# App settings
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=UTC
```

---

## API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/transactions` | List transactions |
| GET | `/api/v1/transactions/{id}` | Get transaction |
| GET | `/api/v1/metrics/overview` | Dashboard metrics |
| GET | `/api/v1/metrics/trends` | Trend data |
| GET | `/api/v1/metrics/by-project` | Per-project metrics |
| GET | `/api/v1/reconciliation/summary` | Recon summary |
| GET | `/api/v1/reconciliation/discrepancies` | Discrepancies |
| POST | `/api/v1/reconciliation/run` | Run reconciliation |
| GET | `/api/v1/export/transactions` | Export CSV/Excel |
| GET | `/api/v1/sync/status` | Sync status |
| POST | `/api/v1/sync/trigger` | Manual sync trigger |
