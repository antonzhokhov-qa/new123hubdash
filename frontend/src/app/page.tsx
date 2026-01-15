"use client";

import { useFilterStore } from "@/stores/filter-store";
import { useMetricsOverview } from "@/hooks/use-metrics";
import { useTransactions } from "@/hooks/use-transactions";
import { KPICard } from "@/components/dashboard/kpi-card";
import { PeriodSelector } from "@/components/dashboard/period-selector";
import { SourceTabs } from "@/components/dashboard/source-tabs";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { SourceBadge } from "@/components/dashboard/source-badge";
import { ChartRow, ChartRowItem } from "@/components/dashboard/chart-row";
import { ChartCard } from "@/components/dashboard/chart-card";
import {
  TrendChartContent,
  HeatmapChartContent,
  HourlyConversionContent,
  AmountDistributionContent,
  ConversionBarContent,
  PeriodComparisonContent,
  GeoChartContent,
  DonutChartContent,
  ProjectBarContent,
} from "@/components/dashboard/chart-wrappers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatNumber, truncateId } from "@/lib/utils";
import { format } from "date-fns";
import {
  Wallet,
  CheckCircle,
  XCircle,
  Percent,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { getDateParams, source } = useFilterStore();
  const dateParams = getDateParams();
  
  const paramsWithSource = {
    ...dateParams,
    ...(source ? { source } : {}),
  };

  const { data: metricsData, isLoading: metricsLoading } = useMetricsOverview(paramsWithSource);
  const { data: recentTxns, isLoading: txnsLoading } = useTransactions({
    ...paramsWithSource,
    limit: 10,
    sort_by: "created_at",
    order: "desc",
  });

  const metrics = metricsData?.data;

  return (
    <div className="space-y-6">
      {/* Header with Global Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
          <p className="text-sm text-text-muted">Overview of your payment operations</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SourceTabs />
          <PeriodSelector />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          label="Total Volume"
          value={metrics ? formatCurrency(metrics.total.amount, metrics.total.currency) : 0}
          subtext={metrics ? `${formatNumber(metrics.total.count)} transactions` : undefined}
          trend={metrics?.trends.total_change}
          icon={Wallet}
          isLoading={metricsLoading}
        />
        <KPICard
          label="Successful"
          value={metrics ? formatCurrency(metrics.by_status.success.amount, "INR") : 0}
          subtext={metrics ? `${formatNumber(metrics.by_status.success.count)} transactions` : undefined}
          trend={metrics?.trends.success_change}
          icon={CheckCircle}
          color="success"
          isLoading={metricsLoading}
        />
        <KPICard
          label="Failed"
          value={metrics ? formatCurrency(metrics.by_status.failed.amount, "INR") : 0}
          subtext={metrics ? `${formatNumber(metrics.by_status.failed.count)} transactions` : undefined}
          trend={metrics?.trends.failed_change}
          icon={XCircle}
          color="failed"
          isLoading={metricsLoading}
        />
        <KPICard
          label="Conversion Rate"
          value={metrics ? `${metrics.conversion_rate.toFixed(1)}%` : "0%"}
          subtext={metrics ? `Avg ticket: ${formatCurrency(metrics.avg_ticket, "INR")}` : undefined}
          icon={Percent}
          color="default"
          isLoading={metricsLoading}
        />
      </div>

      {/* Row 1: Trends & Time Analysis */}
      <ChartRow title="Trends & Time Analysis">
        <ChartRowItem>
          <ChartCard
            title="Transaction Trends"
            filters={{ source: true, period: true, granularity: true, metric: true }}
            defaultGranularity="hour"
            defaultMetric="count"
            metricOptions={[
              { value: "count", label: "Count" },
              { value: "amount", label: "Amount" },
            ]}
            minWidth="450px"
          >
            {(params) => <TrendChartContent params={params} />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="Period Comparison"
            filters={{ source: true, period: true }}
            minWidth="350px"
          >
            {(params) => <PeriodComparisonContent params={params} />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="Hourly Conversion"
            filters={{ source: true, period: true }}
            minWidth="450px"
          >
            {(params) => <HourlyConversionContent params={params} />}
          </ChartCard>
        </ChartRowItem>
      </ChartRow>

      {/* Row 2: Heatmaps & Distributions */}
      <ChartRow title="Heatmaps & Distributions">
        <ChartRowItem>
          <ChartCard
            title="Activity Heatmap"
            filters={{ source: true, period: true, metric: true }}
            defaultMetric="amount"
            metricOptions={[
              { value: "amount", label: "Amount" },
              { value: "count", label: "Count" },
              { value: "conversion", label: "Conversion" },
            ]}
            minWidth="500px"
          >
            {(params) => <HeatmapChartContent params={params} />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="Amount Distribution"
            filters={{ source: true, period: true }}
            minWidth="350px"
          >
            {(params) => <AmountDistributionContent params={params} />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="By Country"
            filters={{ source: true, period: true }}
            minWidth="320px"
          >
            {(params) => <GeoChartContent params={params} />}
          </ChartCard>
        </ChartRowItem>
      </ChartRow>

      {/* Row 3: Merchants & Projects */}
      <ChartRow title="Merchants & Projects">
        <ChartRowItem>
          <ChartCard
            title="Top Merchants"
            filters={{ source: true, period: true, limit: true }}
            defaultLimit={5}
            minWidth="350px"
          >
            {(params) => <ConversionBarContent params={params} showTop={true} />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="Bottom Merchants"
            filters={{ source: true, period: true, limit: true }}
            defaultLimit={5}
            minWidth="350px"
          >
            {(params) => <ConversionBarContent params={params} showTop={false} />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="By Project (Volume)"
            filters={{ source: true, period: true, limit: true }}
            defaultLimit={6}
            minWidth="380px"
          >
            {(params) => <ProjectBarContent params={params} />}
          </ChartCard>
        </ChartRowItem>
      </ChartRow>

      {/* Row 4: Status & Source Breakdown */}
      <ChartRow title="Status & Source Breakdown">
        <ChartRowItem>
          <ChartCard
            title="By Status"
            filters={{ source: true, period: true }}
            minWidth="280px"
          >
            {(params) => <DonutChartContent params={params} type="status" />}
          </ChartCard>
        </ChartRowItem>
        <ChartRowItem>
          <ChartCard
            title="By Source"
            filters={{ period: true }}
            minWidth="280px"
          >
            {(params) => <DonutChartContent params={params} type="source" />}
          </ChartCard>
        </ChartRowItem>
      </ChartRow>

      {/* Recent Transactions */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-medium">Recent Transactions</CardTitle>
          <Link
            href="/transactions"
            className="text-sm text-accent-primary hover:text-accent-hover"
          >
            View all
          </Link>
        </CardHeader>
        <CardContent>
          {txnsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source</TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>Project</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTxns?.data?.map((txn) => (
                  <TableRow key={txn.id}>
                    <TableCell>
                      <SourceBadge source={txn.source} />
                    </TableCell>
                    <TableCell className="font-mono text-xs text-text-secondary">
                      {truncateId(txn.client_operation_id || txn.source_id)}
                    </TableCell>
                    <TableCell className="text-text-secondary">
                      {txn.project || "-"}
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatCurrency(txn.amount, txn.currency)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={txn.status} />
                    </TableCell>
                    <TableCell className="text-text-muted text-sm">
                      {format(new Date(txn.created_at), "HH:mm:ss")}
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
