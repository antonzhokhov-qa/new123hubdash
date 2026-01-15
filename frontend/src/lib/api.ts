const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type Source = "vima" | "payshack" | "all";

export type TransactionStatus = "success" | "pending" | "failed" | "cancelled";

export interface Transaction {
  id: string;
  external_id: string;
  source: Source;
  status: TransactionStatus;
  amount: number;
  amount_usd?: number;
  currency: string;
  merchant_id?: string;
  merchant_name?: string;
  project_id?: string;
  project_name?: string;
  project?: string;
  customer_id?: string;
  payment_method?: string;
  country?: string;
  created_at: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
  // Extended fields
  client_operation_id?: string;
  source_id?: string;
}

export interface MetricsOverview {
  total_transactions: number;
  total_volume: number;
  total_volume_usd: number;
  success_rate: number;
  average_amount: number;
  average_amount_usd: number;
  period_change?: {
    transactions: number;
    volume: number;
    success_rate: number;
  };
  // Extended structure for dashboard
  total: {
    amount: number;
    amount_usd: number;
    count: number;
  };
  by_status: {
    success: { amount: number; amount_usd: number; count: number };
    failed: { amount: number; amount_usd: number; count: number };
    pending: { amount: number; amount_usd: number; count: number };
  };
  trends: {
    total_change: number;
    success_change: number;
    failed_change: number;
  };
  conversion_rate: number;
  avg_ticket: number;
  avg_ticket_usd: number;
}

export interface MetricsByProject {
  project_id: string;
  project_name: string;
  transactions: number;
  volume: number;
  volume_usd: number;
  success_rate: number;
}

export interface MetricsTrend {
  date: string;
  transactions: number;
  volume: number;
  volume_usd: number;
  success_rate: number;
}

export interface SyncStatus {
  source: Source;
  status: "running" | "stopped" | "error" | "idle";
  last_sync_at: string | null;
  last_successful_sync: string | null;
  records_synced: number;
  total_records: number;
  error_message: string | null;
  next_sync_in_seconds: number | null;
}

export interface ReconciliationSummary {
  total_matched: number;
  total_unmatched: number;
  total_discrepancies: number;
  match_rate: number;
  last_reconciliation_at: string | null;
  date?: string;
  total_transactions?: number;
}

export interface ReconciliationSummaryResponse {
  data: ReconciliationSummary;
}

export interface Discrepancy {
  id: string;
  vima_id?: string;
  payshack_id?: string;
  type: "missing_vima" | "missing_payshack" | "amount_mismatch" | "status_mismatch";
  vima_amount?: number;
  payshack_amount?: number;
  difference?: number;
  created_at: string;
}

export interface ConversionByProject {
  project_id: string;
  project_name: string;
  total: number;
  successful: number;
  conversion_rate: number;
}

export interface HourlyDistributionPoint {
  hour: number;
  total: number;
  successful: number;
  conversion_rate: number;
}

export interface CountryMetrics {
  country: string;
  country_code: string;
  transactions: number;
  volume: number;
  volume_usd: number;
  success_rate: number;
}

export interface HeatmapResponse {
  data: Array<{
    day: number;
    hour: number;
    value: number;
  }>;
}

export interface PeriodComparisonResponse {
  current: MetricsOverview;
  previous: MetricsOverview;
  change: {
    transactions: number;
    volume: number;
    success_rate: number;
  };
}

export interface AmountDistribution {
  buckets: AmountBucketPoint[];
}

export interface AmountBucketPoint {
  range: string;
  min: number;
  max: number;
  count: number;
  volume: number;
}

export interface MerchantMetrics {
  merchant_id: string;
  merchant_name: string;
  project: string;
  transactions: number;
  volume: number;
  volume_usd: number;
  success_rate: number;
  projects: string[];
  // Extended fields for merchants page
  total_count: number;
  total_amount: number;
  avg_ticket: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
  conversion_rate: number;
  last_txn_at: string | null;
}

export interface TransactionsResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  // Transactions
  async getTransactions(params?: {
    source?: Source;
    status?: TransactionStatus;
    page?: number;
    page_size?: number;
    start_date?: string;
    end_date?: string;
    search?: string;
    project_id?: string;
    merchant_id?: string;
  }): Promise<TransactionsResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "all") {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return this.request<TransactionsResponse>(
      `/transactions${query ? `?${query}` : ""}`
    );
  }

  // Metrics
  async getMetricsOverview(params?: {
    source?: Source;
    start_date?: string;
    end_date?: string;
    project_id?: string;
  }): Promise<MetricsOverview> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "all") {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return this.request<MetricsOverview>(
      `/metrics/overview${query ? `?${query}` : ""}`
    );
  }

  async getMetricsByProject(params?: {
    source?: Source;
    start_date?: string;
    end_date?: string;
  }): Promise<MetricsByProject[]> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "all") {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return this.request<MetricsByProject[]>(
      `/metrics/by-project${query ? `?${query}` : ""}`
    );
  }

  async getMetricsTrends(params?: {
    source?: Source;
    start_date?: string;
    end_date?: string;
    granularity?: "hour" | "day" | "week" | "month";
  }): Promise<MetricsTrend[]> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "all") {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return this.request<MetricsTrend[]>(
      `/metrics/trends${query ? `?${query}` : ""}`
    );
  }

  // Sync
  async getSyncStatus(): Promise<{ sources: SyncStatus[] }> {
    return this.request<{ sources: SyncStatus[] }>("/sync/status");
  }

  async triggerSync(source: Source): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/sync/trigger/${source}`, {
      method: "POST",
    });
  }

  // Reconciliation
  async getReconciliationSummary(date?: string): Promise<ReconciliationSummaryResponse> {
    const query = date ? `?date=${date}` : "";
    const data = await this.request<ReconciliationSummary>(`/reconciliation/summary${query}`);
    return { data };
  }

  async getDiscrepancies(params?: {
    from_date?: string;
    to_date?: string;
    type?: string;
    page?: number;
    limit?: number;
  }): Promise<{ data: Discrepancy[]; meta: { page: number; limit: number; total: number; total_pages: number } }> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    const result = await this.request<{ items: Discrepancy[]; total: number }>(
      `/reconciliation/discrepancies${query ? `?${query}` : ""}`
    );
    const page = params?.page || 1;
    const limit = params?.limit || 50;
    return {
      data: result.items,
      meta: {
        page,
        limit,
        total: result.total,
        total_pages: Math.ceil(result.total / limit),
      },
    };
  }

  async runReconciliation(date: string): Promise<{ data: { run_id: string; status: string; message: string } }> {
    const result = await this.request<{ run_id: string; status: string; message: string }>(
      `/reconciliation/run`,
      {
        method: "POST",
        body: JSON.stringify({ date }),
      }
    );
    return { data: result };
  }

  // Export
  async exportTransactions(params?: {
    format?: "csv" | "xlsx";
    source?: Source;
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "all") {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    const url = `${this.baseUrl}/export/transactions${query ? `?${query}` : ""}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    return response.blob();
  }
}

export const api = new ApiClient(API_BASE_URL);
