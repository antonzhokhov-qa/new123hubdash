"use client";

import { useState } from "react";
import { useFilterStore } from "@/stores/filter-store";
import { useTransactions } from "@/hooks/use-transactions";
import { FilterPanel } from "@/components/transactions/filter-panel";
import { TransactionTable } from "@/components/transactions/transaction-table";
import { Transaction, api } from "@/lib/api";
import { TransactionDetailModal } from "@/components/transactions/transaction-detail-modal";

export default function TransactionsPage() {
  const { getDateParams, source, project, status, search } = useFilterStore();
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const dateParams = getDateParams();

  const { data, isLoading } = useTransactions({
    ...dateParams,
    source: source || undefined,
    project: project || undefined,
    status: status || undefined,
    search: search || undefined,
    page,
    limit: 50,
    sort_by: sortBy,
    order: sortOrder,
  });

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
  };

  const handleRowClick = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
  };

  const handleExport = async (format: "csv" | "xlsx" = "csv") => {
    setIsExporting(true);
    try {
      const params: Record<string, string> = {
        format,
        ...dateParams,
      };
      if (source) params.source = source;
      if (project) params.project = project;
      if (status) params.status = status;
      if (search) params.search = search;

      const url = api.getExportUrl("transactions", params);
      
      // Trigger download
      const link = document.createElement("a");
      link.href = url;
      link.download = `transactions_${dateParams.from_date}_${dateParams.to_date}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Transactions</h1>
        <p className="text-sm text-text-muted">
          View and manage all payment transactions
        </p>
      </div>

      {/* Filters */}
      <FilterPanel onExport={handleExport} isExporting={isExporting} />

      {/* Table */}
      <TransactionTable
        data={data?.data || []}
        meta={data?.meta}
        isLoading={isLoading}
        onPageChange={setPage}
        onRowClick={handleRowClick}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
      />

      {/* Transaction Detail Modal */}
      {selectedTransaction && (
        <TransactionDetailModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}
    </div>
  );
}
