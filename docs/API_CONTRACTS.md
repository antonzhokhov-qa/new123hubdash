# API Contracts for Frontend

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.yourdomain.com/api/v1
```

## Authentication

> **Note:** Authentication будет добавлена позже. Пока все endpoints публичные.

---

## Common Types

### TypeScript Definitions

```typescript
// Base response wrapper
interface ApiResponse<T> {
  data: T;
  meta?: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

// Transaction source
type Source = 'vima' | 'payshack';

// Transaction status
type TransactionStatus = 'success' | 'failed' | 'pending';

// Currency (ISO 4217)
type Currency = 'INR' | 'USD' | 'EUR';

// Date string (ISO 8601)
type ISODateString = string; // "2026-01-15T15:46:20.195Z"

// Date only
type DateString = string; // "2026-01-15"
```

---

## Endpoints

### 1. Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "ok",
    "redis": "ok"
  }
}
```

---

### 2. Transactions

#### List Transactions

```
GET /transactions
```

**Query Parameters:**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source` | string | No | - | Filter by source: `vima`, `payshack` |
| `project` | string | No | - | Filter by project: `91game`, `monetix`, `caroussel` |
| `status` | string | No | - | Filter by status: `success`, `failed`, `pending` |
| `from_date` | string | No | - | Start date (YYYY-MM-DD) |
| `to_date` | string | No | - | End date (YYYY-MM-DD) |
| `search` | string | No | - | Search by ID, email, phone |
| `page` | int | No | 1 | Page number |
| `limit` | int | No | 50 | Records per page (max 100) |
| `sort_by` | string | No | `created_at` | Sort field |
| `order` | string | No | `desc` | Sort order: `asc`, `desc` |

**Example Request:**
```
GET /transactions?source=vima&status=success&from_date=2026-01-01&to_date=2026-01-15&page=1&limit=50
```

**Response:**
```typescript
interface TransactionListResponse {
  data: Transaction[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

interface Transaction {
  id: string;                      // UUID
  source: Source;
  source_id: string;               // Original ID from source
  reference_id: string | null;     // Vima reference
  client_operation_id: string | null; // c_id for matching
  order_id: string | null;         // PayShack order ID
  
  project: string | null;
  merchant_id: string | null;
  
  amount: number;                  // Decimal, e.g. 100.00
  currency: Currency;
  fee: number | null;
  
  status: TransactionStatus;
  original_status: string | null;
  
  user_id: string | null;
  user_email: string | null;
  user_phone: string | null;
  user_name: string | null;
  country: string | null;          // 2-letter code
  
  utr: string | null;              // PayShack UTR
  
  payment_method: string | null;
  payment_product: string | null;
  
  created_at: ISODateString;
  updated_at: ISODateString | null;
  completed_at: ISODateString | null;
}
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source": "vima",
      "source_id": "1067250921664811008",
      "reference_id": "019bc256-159f-72f3-b2c2-7506937517be",
      "client_operation_id": "1768491979464",
      "order_id": null,
      "project": "91game",
      "merchant_id": null,
      "amount": 100.00,
      "currency": "INR",
      "fee": 0.00,
      "status": "success",
      "original_status": "success",
      "user_id": "16faca55460b41c3a9b46a736c8dbfed",
      "user_email": "sumit74360zne@gmail.com",
      "user_phone": "9768493341",
      "user_name": "Sumit Bhatt",
      "country": "IN",
      "utr": null,
      "payment_method": "apm",
      "payment_product": "multihub-api",
      "created_at": "2026-01-15T15:46:20.195Z",
      "updated_at": "2026-01-15T15:46:46.487Z",
      "completed_at": "2026-01-15T15:46:43.817Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 15420,
    "total_pages": 309
  }
}
```

#### Get Transaction by ID

```
GET /transactions/{id}
```

**Response:**
```typescript
interface TransactionDetailResponse {
  data: Transaction & {
    raw_data: Record<string, any>;  // Original JSON from source
  };
}
```

---

### 3. Metrics

#### Overview Metrics

```
GET /metrics/overview
```

**Query Parameters:**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from_date` | string | No | Today | Start date |
| `to_date` | string | No | Today | End date |
| `source` | string | No | - | Filter by source |
| `project` | string | No | - | Filter by project |
| `timezone` | string | No | UTC | Timezone for date calculations |

**Response:**
```typescript
interface MetricsOverviewResponse {
  data: {
    period: {
      from: DateString;
      to: DateString;
    };
    total: {
      count: number;
      amount: number;
      currency: Currency;
    };
    by_status: {
      success: { count: number; amount: number };
      failed: { count: number; amount: number };
      pending: { count: number; amount: number };
    };
    by_source: {
      vima: { count: number; amount: number };
      payshack: { count: number; amount: number };
    };
    conversion_rate: number;    // Percentage, e.g. 92.1
    avg_ticket: number;         // Average transaction amount
    trends: {
      total_change: number;     // % change vs previous period
      success_change: number;
      failed_change: number;
    };
  };
}
```

**Example Response:**
```json
{
  "data": {
    "period": {
      "from": "2026-01-15",
      "to": "2026-01-15"
    },
    "total": {
      "count": 15420,
      "amount": 1542000.00,
      "currency": "INR"
    },
    "by_status": {
      "success": { "count": 14200, "amount": 1420000.00 },
      "failed": { "count": 1100, "amount": 110000.00 },
      "pending": { "count": 120, "amount": 12000.00 }
    },
    "by_source": {
      "vima": { "count": 10200, "amount": 1020000.00 },
      "payshack": { "count": 5220, "amount": 522000.00 }
    },
    "conversion_rate": 92.1,
    "avg_ticket": 100.00,
    "trends": {
      "total_change": 12.5,
      "success_change": 15.2,
      "failed_change": -8.1
    }
  }
}
```

#### Metrics by Project

```
GET /metrics/by-project
```

**Query Parameters:** Same as overview

**Response:**
```typescript
interface MetricsByProjectResponse {
  data: {
    period: { from: DateString; to: DateString };
    projects: Array<{
      project: string;
      count: number;
      amount: number;
      success_rate: number;
    }>;
  };
}
```

**Example Response:**
```json
{
  "data": {
    "period": { "from": "2026-01-15", "to": "2026-01-15" },
    "projects": [
      { "project": "91game", "count": 10025, "amount": 1002500.00, "success_rate": 93.5 },
      { "project": "monetix", "count": 3855, "amount": 385500.00, "success_rate": 91.2 },
      { "project": "caroussel", "count": 1540, "amount": 154000.00, "success_rate": 89.8 }
    ]
  }
}
```

#### Metrics Trends (for charts)

```
GET /metrics/trends
```

**Query Parameters:**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from_date` | string | Yes | - | Start date |
| `to_date` | string | Yes | - | End date |
| `granularity` | string | No | `hour` | `hour`, `day`, `week` |
| `source` | string | No | - | Filter by source |
| `project` | string | No | - | Filter by project |

**Response:**
```typescript
interface MetricsTrendsResponse {
  data: {
    period: { from: DateString; to: DateString };
    granularity: 'hour' | 'day' | 'week';
    points: Array<{
      timestamp: ISODateString;
      count: number;
      amount: number;
      success_count: number;
      failed_count: number;
    }>;
  };
}
```

**Example Response:**
```json
{
  "data": {
    "period": { "from": "2026-01-15", "to": "2026-01-15" },
    "granularity": "hour",
    "points": [
      { "timestamp": "2026-01-15T00:00:00Z", "count": 450, "amount": 45000.00, "success_count": 420, "failed_count": 25 },
      { "timestamp": "2026-01-15T01:00:00Z", "count": 380, "amount": 38000.00, "success_count": 355, "failed_count": 20 },
      { "timestamp": "2026-01-15T02:00:00Z", "count": 520, "amount": 52000.00, "success_count": 485, "failed_count": 30 }
    ]
  }
}
```

---

### 4. Reconciliation

#### Get Reconciliation Summary

```
GET /reconciliation/summary
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | Yes | Date for reconciliation (YYYY-MM-DD) |

**Response:**
```typescript
interface ReconciliationSummaryResponse {
  data: {
    date: DateString;
    run_id: string | null;
    run_at: ISODateString | null;
    
    total_transactions: number;
    
    matched: {
      count: number;
      percentage: number;
    };
    
    discrepancies: {
      count: number;
      percentage: number;
      by_type: {
        amount: number;
        status: number;
      };
    };
    
    missing: {
      count: number;
      percentage: number;
      missing_vima: number;
      missing_payshack: number;
    };
  };
}
```

**Example Response:**
```json
{
  "data": {
    "date": "2026-01-15",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "run_at": "2026-01-15T22:00:00Z",
    "total_transactions": 1240,
    "matched": {
      "count": 1180,
      "percentage": 95.2
    },
    "discrepancies": {
      "count": 35,
      "percentage": 2.8,
      "by_type": {
        "amount": 20,
        "status": 15
      }
    },
    "missing": {
      "count": 25,
      "percentage": 2.0,
      "missing_vima": 10,
      "missing_payshack": 15
    }
  }
}
```

#### Get Discrepancies List

```
GET /reconciliation/discrepancies
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `from_date` | string | No | Start date |
| `to_date` | string | No | End date |
| `type` | string | No | Filter: `amount`, `status`, `missing_vima`, `missing_payshack` |
| `page` | int | No | Page number |
| `limit` | int | No | Records per page |

**Response:**
```typescript
interface DiscrepanciesResponse {
  data: Discrepancy[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

interface Discrepancy {
  id: string;
  recon_date: DateString;
  client_operation_id: string;
  
  match_status: 'discrepancy' | 'missing_vima' | 'missing_payshack';
  discrepancy_type: 'amount' | 'status' | 'time' | 'missing' | null;
  
  vima_txn_id: string | null;
  payshack_txn_id: string | null;
  
  vima_amount: number | null;
  payshack_amount: number | null;
  amount_diff: number | null;
  
  vima_status: string | null;
  payshack_status: string | null;
  
  created_at: ISODateString;
}
```

#### Run Reconciliation

```
POST /reconciliation/run
```

**Request Body:**
```json
{
  "date": "2026-01-15"
}
```

**Response:**
```typescript
interface RunReconciliationResponse {
  data: {
    run_id: string;
    status: 'started' | 'completed' | 'failed';
    message: string;
  };
}
```

---

### 5. Sync Status

#### Get Sync Status

```
GET /sync/status
```

**Response:**
```typescript
interface SyncStatusResponse {
  data: {
    sources: Array<{
      source: Source;
      status: 'idle' | 'running' | 'failed';
      last_sync_at: ISODateString | null;
      last_successful_sync: ISODateString | null;
      records_synced: number;
      next_sync_at: ISODateString | null;
      error_message: string | null;
      last_cursor: string | null;
    }>;
  };
}
```

**Example Response:**
```json
{
  "data": {
    "sources": [
      {
        "source": "vima",
        "status": "idle",
        "last_sync_at": "2026-01-15T21:15:00Z",
        "last_successful_sync": "2026-01-15T21:15:00Z",
        "records_synced": 15420,
        "next_sync_at": "2026-01-15T21:20:00Z",
        "error_message": null,
        "last_cursor": "1067251098160838656"
      },
      {
        "source": "payshack",
        "status": "idle",
        "last_sync_at": "2026-01-15T21:08:00Z",
        "last_successful_sync": "2026-01-15T21:08:00Z",
        "records_synced": 5220,
        "next_sync_at": "2026-01-15T21:18:00Z",
        "error_message": null,
        "last_cursor": null
      }
    ]
  }
}
```

#### Trigger Manual Sync

```
POST /sync/trigger
```

**Request Body:**
```json
{
  "source": "vima"  // or "payshack" or null for all
}
```

**Response:**
```typescript
interface TriggerSyncResponse {
  data: {
    source: Source | 'all';
    status: 'triggered';
    message: string;
  };
}
```

---

### 6. Export

#### Export Transactions

```
GET /export/transactions
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | string | No | `csv` (default), `xlsx` |
| `from_date` | string | No | Start date |
| `to_date` | string | No | End date |
| `source` | string | No | Filter by source |
| `project` | string | No | Filter by project |
| `status` | string | No | Filter by status |

**Response:** File download (Content-Disposition: attachment)

#### Export Reconciliation

```
GET /export/reconciliation
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | string | No | `csv` (default), `xlsx` |
| `date` | string | Yes | Reconciliation date |
| `type` | string | No | Filter discrepancy type |

**Response:** File download

---

## Error Handling

### Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
```

### Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request parameters |
| 404 | `NOT_FOUND` | Resource not found |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 502 | `UPSTREAM_ERROR` | Error from Vima/PayShack API |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

**Example Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": {
      "field": "from_date",
      "expected": "YYYY-MM-DD",
      "received": "15-01-2026"
    }
  }
}
```

---

## Frontend API Client Example

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(error.error.code, error.error.message);
    }

    return response.json();
  }

  // Transactions
  async getTransactions(params: TransactionParams) {
    const query = new URLSearchParams(params as any).toString();
    return this.request<TransactionListResponse>(`/transactions?${query}`);
  }

  async getTransaction(id: string) {
    return this.request<TransactionDetailResponse>(`/transactions/${id}`);
  }

  // Metrics
  async getMetricsOverview(params: MetricsParams) {
    const query = new URLSearchParams(params as any).toString();
    return this.request<MetricsOverviewResponse>(`/metrics/overview?${query}`);
  }

  async getMetricsTrends(params: TrendsParams) {
    const query = new URLSearchParams(params as any).toString();
    return this.request<MetricsTrendsResponse>(`/metrics/trends?${query}`);
  }

  // Reconciliation
  async getReconciliationSummary(date: string) {
    return this.request<ReconciliationSummaryResponse>(
      `/reconciliation/summary?date=${date}`
    );
  }

  async getDiscrepancies(params: DiscrepancyParams) {
    const query = new URLSearchParams(params as any).toString();
    return this.request<DiscrepanciesResponse>(`/reconciliation/discrepancies?${query}`);
  }

  async runReconciliation(date: string) {
    return this.request<RunReconciliationResponse>('/reconciliation/run', {
      method: 'POST',
      body: JSON.stringify({ date }),
    });
  }

  // Sync
  async getSyncStatus() {
    return this.request<SyncStatusResponse>('/sync/status');
  }

  async triggerSync(source?: Source) {
    return this.request<TriggerSyncResponse>('/sync/trigger', {
      method: 'POST',
      body: JSON.stringify({ source }),
    });
  }
}

export const api = new ApiClient();
```

---

## React Query Hooks Example

```typescript
// hooks/use-transactions.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useTransactions(params: TransactionParams) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: () => api.getTransactions(params),
    staleTime: 30_000, // 30 seconds
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: () => api.getTransaction(id),
    enabled: !!id,
  });
}

// hooks/use-metrics.ts
export function useMetricsOverview(params: MetricsParams) {
  return useQuery({
    queryKey: ['metrics', 'overview', params],
    queryFn: () => api.getMetricsOverview(params),
    staleTime: 60_000, // 1 minute
    refetchInterval: 60_000, // Auto-refresh every minute
  });
}

export function useMetricsTrends(params: TrendsParams) {
  return useQuery({
    queryKey: ['metrics', 'trends', params],
    queryFn: () => api.getMetricsTrends(params),
    staleTime: 5 * 60_000, // 5 minutes
  });
}
```
