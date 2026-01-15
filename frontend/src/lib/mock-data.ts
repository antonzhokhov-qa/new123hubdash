import type {
  Transaction,
  MetricsOverview,
  MetricsByProject,
  MetricsTrend,
  SyncStatus,
  ReconciliationSummary,
  Discrepancy,
} from "./api";

export const mockMetricsOverview: MetricsOverview = {
  total_transactions: 15234,
  total_volume: 2456789.50,
  total_volume_usd: 2456789.50,
  success_rate: 87.5,
  average_amount: 161.25,
  average_amount_usd: 161.25,
  period_change: {
    transactions: 12.5,
    volume: 8.3,
    success_rate: 2.1,
  },
};

export const mockMetricsByProject: MetricsByProject[] = [
  {
    project_id: "proj_001",
    project_name: "Main Checkout",
    transactions: 8500,
    volume: 1250000,
    volume_usd: 1250000,
    success_rate: 89.2,
  },
  {
    project_id: "proj_002",
    project_name: "Mobile App",
    transactions: 4200,
    volume: 780000,
    volume_usd: 780000,
    success_rate: 85.7,
  },
  {
    project_id: "proj_003",
    project_name: "API Direct",
    transactions: 2534,
    volume: 426789.50,
    volume_usd: 426789.50,
    success_rate: 91.3,
  },
];

export const mockMetricsTrends: MetricsTrend[] = Array.from({ length: 7 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (6 - i));
  return {
    date: date.toISOString().split("T")[0],
    transactions: Math.floor(Math.random() * 500) + 1500,
    volume: Math.floor(Math.random() * 100000) + 200000,
    volume_usd: Math.floor(Math.random() * 100000) + 200000,
    success_rate: Math.random() * 10 + 85,
  };
});

export const mockSyncStatus: SyncStatus[] = [
  {
    source: "vima",
    status: "running",
    last_sync_at: new Date().toISOString(),
    last_successful_sync: new Date().toISOString(),
    records_synced: 15234,
    total_records: 15234,
    error_message: null,
    next_sync_in_seconds: 25,
  },
  {
    source: "payshack",
    status: "running",
    last_sync_at: new Date().toISOString(),
    last_successful_sync: new Date().toISOString(),
    records_synced: 12456,
    total_records: 12456,
    error_message: null,
    next_sync_in_seconds: 180,
  },
];

export const mockReconciliationSummary: ReconciliationSummary = {
  total_matched: 11234,
  total_unmatched: 456,
  total_discrepancies: 23,
  match_rate: 96.1,
  last_reconciliation_at: new Date().toISOString(),
  total_transactions: 11713,
  matched: {
    count: 11234,
    percentage: 96.1,
  },
  discrepancies: {
    count: 23,
    by_type: {
      amount: 15,
      status: 8,
    },
  },
  missing: {
    count: 456,
    missing_vima: 234,
    missing_payshack: 222,
  },
  run_at: new Date().toISOString(),
};

export const mockDiscrepancies: (Discrepancy & { discrepancy_type?: string; match_status?: string })[] = [
  {
    id: "disc_001",
    vima_id: "vima_tx_12345",
    payshack_id: "ps_tx_12345",
    type: "amount_mismatch",
    discrepancy_type: "amount_mismatch",
    match_status: "mismatched",
    vima_amount: 1500.00,
    payshack_amount: 1495.00,
    difference: 5.00,
    created_at: new Date().toISOString(),
  },
  {
    id: "disc_002",
    vima_id: "vima_tx_12346",
    type: "missing_payshack",
    discrepancy_type: "missing_payshack",
    match_status: "unmatched",
    vima_amount: 2300.00,
    created_at: new Date().toISOString(),
  },
  {
    id: "disc_003",
    payshack_id: "ps_tx_12347",
    type: "missing_vima",
    discrepancy_type: "missing_vima",
    match_status: "unmatched",
    payshack_amount: 890.00,
    created_at: new Date().toISOString(),
  },
];

export const mockTransactions: Transaction[] = Array.from({ length: 50 }, (_, i) => ({
  id: `tx_${String(i + 1).padStart(5, "0")}`,
  external_id: `ext_${Math.random().toString(36).substr(2, 9)}`,
  source: i % 2 === 0 ? "vima" : "payshack",
  status: ["success", "pending", "failed", "cancelled"][Math.floor(Math.random() * 4)] as Transaction["status"],
  amount: Math.floor(Math.random() * 5000) + 100,
  amount_usd: Math.floor(Math.random() * 5000) + 100,
  currency: ["INR", "USD", "EUR"][Math.floor(Math.random() * 3)],
  merchant_id: `merch_${Math.floor(Math.random() * 10) + 1}`,
  merchant_name: `Merchant ${Math.floor(Math.random() * 10) + 1}`,
  project_id: `proj_${Math.floor(Math.random() * 5) + 1}`,
  project_name: `Project ${Math.floor(Math.random() * 5) + 1}`,
  customer_id: `cust_${Math.random().toString(36).substr(2, 8)}`,
  payment_method: ["upi", "card", "netbanking", "wallet"][Math.floor(Math.random() * 4)],
  country: ["IN", "US", "GB", "DE"][Math.floor(Math.random() * 4)],
  created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
}));
