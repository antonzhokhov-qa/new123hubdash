"use client";

import { useState } from "react";
import { useFilterStore } from "@/stores/filter-store";
import { useMerchants, useConversionByProject } from "@/hooks/use-metrics";
import { SourceTabs } from "@/components/dashboard/source-tabs";
import { PeriodSelector } from "@/components/dashboard/period-selector";
import { KPICard } from "@/components/dashboard/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";
import { format } from "date-fns";
import {
  Store,
  TrendingUp,
  TrendingDown,
  Search,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { MerchantMetrics } from "@/lib/api";

function getConversionColor(rate: number): string {
  if (rate >= 90) return "text-status-success";
  if (rate >= 70) return "text-status-pending";
  return "text-status-failed";
}

function getConversionBg(rate: number): string {
  if (rate >= 90) return "bg-status-success/10";
  if (rate >= 70) return "bg-status-pending/10";
  return "bg-status-failed/10";
}

export default function MerchantsPage() {
  const { getDateParams, source } = useFilterStore();
  const dateParams = getDateParams();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"total_amount" | "total_count" | "conversion_rate">("total_amount");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedMerchant, setSelectedMerchant] = useState<MerchantMetrics | null>(null);

  const { data: merchantsData, isLoading } = useMerchants({
    ...dateParams,
    source: source || undefined,
    search: search || undefined,
    sort_by: sortBy,
    order: sortOrder,
    page,
    limit: 20,
  });

  const { data: conversionData, isLoading: conversionLoading } = useConversionByProject({
    ...dateParams,
    source: source || undefined,
  });

  const merchants = merchantsData?.data?.merchants || [];
  const totalMerchants = merchantsData?.data?.total || 0;
  const totalPages = merchantsData?.data?.pages || 1;
  const top5 = conversionData?.data?.top_5 || [];
  const bottom5 = conversionData?.data?.bottom_5 || [];

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Merchants</h1>
          <p className="text-sm text-text-muted">
            Detailed analytics by merchant / project
          </p>
        </div>
        <div className="flex items-center gap-3">
          <SourceTabs />
          <PeriodSelector />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          label="Total Merchants"
          value={formatNumber(totalMerchants)}
          icon={Store}
          isLoading={isLoading}
        />
        <KPICard
          label="Top Performer"
          value={top5[0]?.project || "N/A"}
          subtext={top5[0] ? `${top5[0].conversion_rate.toFixed(1)}% conversion` : undefined}
          icon={TrendingUp}
          color="success"
          isLoading={conversionLoading}
        />
        <KPICard
          label="Needs Attention"
          value={bottom5[bottom5.length - 1]?.project || "N/A"}
          subtext={bottom5[bottom5.length - 1] ? `${bottom5[bottom5.length - 1].conversion_rate.toFixed(1)}% conversion` : undefined}
          icon={TrendingDown}
          color="failed"
          isLoading={conversionLoading}
        />
        <KPICard
          label="Avg Conversion"
          value={
            conversionData?.data?.projects.length
              ? `${(
                  conversionData.data.projects.reduce((s, p) => s + p.conversion_rate, 0) /
                  conversionData.data.projects.length
                ).toFixed(1)}%`
              : "0%"
          }
          isLoading={conversionLoading}
        />
      </div>

      {/* Top/Bottom 5 Quick View */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Top 5 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-status-success" />
              Top 5 by Conversion
            </CardTitle>
          </CardHeader>
          <CardContent>
            {conversionLoading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {top5.map((m, i) => (
                  <div
                    key={m.project}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-background-secondary cursor-pointer"
                    onClick={() => setSelectedMerchant(m as any)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-text-muted w-5">
                        #{i + 1}
                      </span>
                      <span className="font-medium text-text-primary">{m.project}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-text-muted">
                        {formatNumber(m.total_count)} txns
                      </span>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-sm font-medium",
                          getConversionBg(m.conversion_rate),
                          getConversionColor(m.conversion_rate)
                        )}
                      >
                        {m.conversion_rate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Bottom 5 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-status-failed" />
              Bottom 5 by Conversion
            </CardTitle>
          </CardHeader>
          <CardContent>
            {conversionLoading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {bottom5.slice().reverse().map((m, i) => (
                  <div
                    key={m.project}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-background-secondary cursor-pointer"
                    onClick={() => setSelectedMerchant(m as any)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-text-muted w-5">
                        #{i + 1}
                      </span>
                      <span className="font-medium text-text-primary">{m.project}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-text-muted">
                        {formatNumber(m.total_count)} txns
                      </span>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-sm font-medium",
                          getConversionBg(m.conversion_rate),
                          getConversionColor(m.conversion_rate)
                        )}
                      >
                        {m.conversion_rate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Merchants Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-medium">All Merchants</CardTitle>
          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <Input
                placeholder="Search merchant..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-9 w-64"
              />
            </div>
            {/* Sort */}
            <Select
              value={sortBy}
              onValueChange={(v) => handleSort(v as typeof sortBy)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="total_amount">By Volume</SelectItem>
                <SelectItem value="total_count">By Transactions</SelectItem>
                <SelectItem value="conversion_rate">By Conversion</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
            >
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Merchant</TableHead>
                    <TableHead className="text-right">Transactions</TableHead>
                    <TableHead className="text-right">Volume</TableHead>
                    <TableHead className="text-right">Avg Ticket</TableHead>
                    <TableHead className="text-right">Success</TableHead>
                    <TableHead className="text-right">Failed</TableHead>
                    <TableHead className="text-right">Conversion</TableHead>
                    <TableHead className="text-right">Last Activity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {merchants.map((m) => (
                    <TableRow
                      key={m.merchant_id}
                      className="cursor-pointer hover:bg-background-secondary"
                      onClick={() => setSelectedMerchant(m)}
                    >
                      <TableCell className="font-medium">{m.project}</TableCell>
                      <TableCell className="text-right">
                        {formatNumber(m.total_count)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(m.total_amount, "INR")}
                      </TableCell>
                      <TableCell className="text-right text-text-secondary">
                        {formatCurrency(m.avg_ticket, "INR")}
                      </TableCell>
                      <TableCell className="text-right text-status-success">
                        {formatNumber(m.success_count)}
                      </TableCell>
                      <TableCell className="text-right text-status-failed">
                        {formatNumber(m.failed_count)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-sm font-medium",
                            getConversionBg(m.conversion_rate),
                            getConversionColor(m.conversion_rate)
                          )}
                        >
                          {m.conversion_rate.toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-text-muted text-sm">
                        {m.last_txn_at
                          ? format(new Date(m.last_txn_at), "MMM dd, HH:mm")
                          : "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-primary">
                <p className="text-sm text-text-muted">
                  Showing {(page - 1) * 20 + 1}-{Math.min(page * 20, totalMerchants)} of{" "}
                  {totalMerchants} merchants
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-text-secondary px-2">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* TODO: Merchant Detail Modal */}
      {selectedMerchant && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background-primary rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-text-primary">
                {selectedMerchant.project}
              </h2>
              <Button variant="outline" size="sm" onClick={() => setSelectedMerchant(null)}>
                Close
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-background-secondary">
                <p className="text-sm text-text-muted">Total Volume</p>
                <p className="text-2xl font-bold text-text-primary">
                  {formatCurrency(selectedMerchant.total_amount, "INR")}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-background-secondary">
                <p className="text-sm text-text-muted">Transactions</p>
                <p className="text-2xl font-bold text-text-primary">
                  {formatNumber(selectedMerchant.total_count)}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-background-secondary">
                <p className="text-sm text-text-muted">Conversion Rate</p>
                <p className={cn("text-2xl font-bold", getConversionColor(selectedMerchant.conversion_rate))}>
                  {selectedMerchant.conversion_rate.toFixed(1)}%
                </p>
              </div>
              <div className="p-4 rounded-lg bg-background-secondary">
                <p className="text-sm text-text-muted">Average Ticket</p>
                <p className="text-2xl font-bold text-text-primary">
                  {formatCurrency(selectedMerchant.avg_ticket, "INR")}
                </p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-lg bg-status-success/10">
                <p className="text-sm text-text-muted">Success</p>
                <p className="text-lg font-semibold text-status-success">
                  {formatNumber(selectedMerchant.success_count)}
                </p>
              </div>
              <div className="text-center p-3 rounded-lg bg-status-failed/10">
                <p className="text-sm text-text-muted">Failed</p>
                <p className="text-lg font-semibold text-status-failed">
                  {formatNumber(selectedMerchant.failed_count)}
                </p>
              </div>
              <div className="text-center p-3 rounded-lg bg-status-pending/10">
                <p className="text-sm text-text-muted">Pending</p>
                <p className="text-lg font-semibold text-status-pending">
                  {formatNumber(selectedMerchant.pending_count)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
