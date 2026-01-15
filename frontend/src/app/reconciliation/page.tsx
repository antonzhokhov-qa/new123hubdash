"use client";

import { useState } from "react";
import { format } from "date-fns";
import { useReconciliationSummary, useDiscrepancies, useRunReconciliation } from "@/hooks/use-reconciliation";
import { KPICard } from "@/components/dashboard/kpi-card";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCurrency, formatNumber, truncateId, cn } from "@/lib/utils";
import {
  CheckCircle,
  AlertTriangle,
  HelpCircle,
  RefreshCw,
  Download,
  Calendar,
} from "lucide-react";

export default function ReconciliationPage() {
  const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  const { data: summaryData, isLoading: summaryLoading } = useReconciliationSummary(selectedDate);
  const { data: discrepanciesData, isLoading: discrepanciesLoading } = useDiscrepancies({
    from_date: selectedDate,
    to_date: selectedDate,
    type: typeFilter || undefined,
  });
  const runReconciliation = useRunReconciliation();

  const summary = summaryData?.data;
  const discrepancies = discrepanciesData?.data || [];

  const handleRunReconciliation = () => {
    runReconciliation.mutate(selectedDate);
  };

  const getDiscrepancyBadge = (type: string | null) => {
    switch (type) {
      case "amount":
        return <span className="text-status-pending">Amount Mismatch</span>;
      case "status":
        return <span className="text-status-failed">Status Mismatch</span>;
      case "missing":
        return <span className="text-text-muted">Missing</span>;
      default:
        return <span className="text-text-muted">{type}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Reconciliation</h1>
          <p className="text-sm text-text-muted">
            Match and verify transactions between Vima and PayShack
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Date selector */}
          <div className="flex items-center gap-2 rounded-lg bg-background-secondary px-3 py-2 border border-border-primary">
            <Calendar className="h-4 w-4 text-text-muted" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-transparent text-sm text-text-primary focus:outline-none"
            />
          </div>
          <Button
            variant="outline"
            onClick={handleRunReconciliation}
            disabled={runReconciliation.isPending}
            className="gap-2"
          >
            <RefreshCw
              className={cn("h-4 w-4", runReconciliation.isPending && "animate-spin")}
            />
            Run Reconciliation
          </Button>
          <Button variant="outline" className="gap-2">
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          label="Total Transactions"
          value={summary ? formatNumber(summary.total_transactions) : 0}
          subtext="For selected date"
          icon={Calendar}
          isLoading={summaryLoading}
        />
        <KPICard
          label="Matched"
          value={summary ? formatNumber(summary.matched.count) : 0}
          subtext={summary ? `${summary.matched.percentage.toFixed(1)}% match rate` : undefined}
          icon={CheckCircle}
          color="success"
          isLoading={summaryLoading}
        />
        <KPICard
          label="Discrepancies"
          value={summary ? formatNumber(summary.discrepancies.count) : 0}
          subtext={
            summary
              ? `${summary.discrepancies.by_type.amount} amount, ${summary.discrepancies.by_type.status} status`
              : undefined
          }
          icon={AlertTriangle}
          color="pending"
          isLoading={summaryLoading}
        />
        <KPICard
          label="Missing"
          value={summary ? formatNumber(summary.missing.count) : 0}
          subtext={
            summary
              ? `${summary.missing.missing_vima} Vima, ${summary.missing.missing_payshack} PayShack`
              : undefined
          }
          icon={HelpCircle}
          color="failed"
          isLoading={summaryLoading}
        />
      </div>

      {/* Last run info */}
      {summary?.run_at && (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <CheckCircle className="h-4 w-4 text-status-success" />
          Last reconciliation run: {format(new Date(summary.run_at), "MMM dd, yyyy HH:mm:ss")}
        </div>
      )}

      {/* Discrepancies Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-medium">Discrepancies</CardTitle>
          <Select
            value={typeFilter || "all"}
            onValueChange={(v) => setTypeFilter(v === "all" ? null : v)}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="amount">Amount Mismatch</SelectItem>
              <SelectItem value="status">Status Mismatch</SelectItem>
              <SelectItem value="missing_vima">Missing in Vima</SelectItem>
              <SelectItem value="missing_payshack">Missing in PayShack</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          {discrepanciesLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : discrepancies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <CheckCircle className="h-12 w-12 text-status-success mb-4" />
              <p className="text-lg font-medium text-text-primary">No discrepancies found</p>
              <p className="text-sm text-text-muted mt-1">
                All transactions matched successfully
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Client Operation ID</TableHead>
                  <TableHead>Vima Amount</TableHead>
                  <TableHead>PayShack Amount</TableHead>
                  <TableHead>Difference</TableHead>
                  <TableHead>Vima Status</TableHead>
                  <TableHead>PayShack Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {discrepancies.map((disc) => (
                  <TableRow key={disc.id}>
                    <TableCell>{getDiscrepancyBadge(disc.discrepancy_type)}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {truncateId(disc.client_operation_id, 16)}
                    </TableCell>
                    <TableCell>
                      {disc.vima_amount !== null
                        ? formatCurrency(disc.vima_amount, "INR")
                        : "-"}
                    </TableCell>
                    <TableCell>
                      {disc.payshack_amount !== null
                        ? formatCurrency(disc.payshack_amount, "INR")
                        : "-"}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "font-medium",
                        disc.amount_diff && disc.amount_diff !== 0
                          ? "text-status-failed"
                          : "text-text-muted"
                      )}
                    >
                      {disc.amount_diff !== null
                        ? formatCurrency(Math.abs(disc.amount_diff), "INR")
                        : "-"}
                    </TableCell>
                    <TableCell>
                      {disc.vima_status ? (
                        <StatusBadge status={disc.vima_status} showIcon={false} />
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>
                      {disc.payshack_status ? (
                        <StatusBadge status={disc.payshack_status} showIcon={false} />
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
