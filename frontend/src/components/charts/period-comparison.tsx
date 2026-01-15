"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PeriodComparisonResponse } from "@/lib/api";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

interface PeriodComparisonProps {
  title: string;
  data?: PeriodComparisonResponse;
  isLoading?: boolean;
  comparisonType?: "day" | "week" | "month";
}

function formatChange(value: number, suffix: string = "%"): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}${suffix}`;
}

function ChangeIndicator({ 
  value, 
  inverse = false 
}: { 
  value: number; 
  inverse?: boolean;
}) {
  const isPositive = inverse ? value < 0 : value > 0;
  const isNegative = inverse ? value > 0 : value < 0;

  if (Math.abs(value) < 0.1) {
    return (
      <div className="flex items-center gap-1 text-text-muted">
        <Minus className="h-4 w-4" />
        <span className="text-sm">No change</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-center gap-1",
        isPositive && "text-status-success",
        isNegative && "text-status-failed"
      )}
    >
      {isPositive ? (
        <ArrowUp className="h-4 w-4" />
      ) : (
        <ArrowDown className="h-4 w-4" />
      )}
      <span className="text-sm font-medium">{formatChange(value)}</span>
    </div>
  );
}

interface MetricRowProps {
  label: string;
  current: number | string;
  previous: number | string;
  change: number;
  inverse?: boolean;
}

function MetricRow({ label, current, previous, change, inverse }: MetricRowProps) {
  return (
    <div className="grid grid-cols-4 gap-4 py-3 border-b border-border-primary last:border-0">
      <div className="text-sm text-text-secondary">{label}</div>
      <div className="text-sm font-medium text-text-primary text-right">{current}</div>
      <div className="text-sm text-text-muted text-right">{previous}</div>
      <div className="flex justify-end">
        <ChangeIndicator value={change} inverse={inverse} />
      </div>
    </div>
  );
}

export function PeriodComparison({
  title,
  data,
  isLoading,
  comparisonType = "day",
}: PeriodComparisonProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px] text-text-muted">
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  const periodLabels = {
    day: { current: "Today", previous: "Yesterday" },
    week: { current: "This Week", previous: "Last Week" },
    month: { current: "This Month", previous: "Last Month" },
  };

  const labels = periodLabels[comparisonType];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Header */}
        <div className="grid grid-cols-4 gap-4 pb-2 border-b border-border-primary mb-2">
          <div className="text-xs text-text-muted uppercase tracking-wide">Metric</div>
          <div className="text-xs text-text-muted uppercase tracking-wide text-right">
            {labels.current}
          </div>
          <div className="text-xs text-text-muted uppercase tracking-wide text-right">
            {labels.previous}
          </div>
          <div className="text-xs text-text-muted uppercase tracking-wide text-right">
            Change
          </div>
        </div>

        {/* Metrics */}
        <MetricRow
          label="Volume"
          current={formatCurrency(data.current.total_amount, "INR")}
          previous={formatCurrency(data.previous.total_amount, "INR")}
          change={data.comparison.amount_change_percent}
        />
        <MetricRow
          label="Transactions"
          current={formatNumber(data.current.total_count)}
          previous={formatNumber(data.previous.total_count)}
          change={data.comparison.count_change_percent}
        />
        <MetricRow
          label="Conversion Rate"
          current={`${data.current.conversion_rate.toFixed(1)}%`}
          previous={`${data.previous.conversion_rate.toFixed(1)}%`}
          change={data.comparison.conversion_change}
        />
        <MetricRow
          label="Avg Ticket"
          current={formatCurrency(data.current.avg_ticket, "INR")}
          previous={formatCurrency(data.previous.avg_ticket, "INR")}
          change={data.comparison.avg_ticket_change_percent}
        />
        <MetricRow
          label="Success"
          current={formatNumber(data.current.success_count)}
          previous={formatNumber(data.previous.success_count)}
          change={
            data.previous.success_count > 0
              ? ((data.current.success_count - data.previous.success_count) / data.previous.success_count) * 100
              : 0
          }
        />
        <MetricRow
          label="Failed"
          current={formatNumber(data.current.failed_count)}
          previous={formatNumber(data.previous.failed_count)}
          change={
            data.previous.failed_count > 0
              ? ((data.current.failed_count - data.previous.failed_count) / data.previous.failed_count) * 100
              : 0
          }
          inverse={true}
        />

        {/* Summary bar */}
        <div className="mt-4 pt-4 border-t border-border-primary">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-text-muted">Period</p>
              <p className="text-sm text-text-secondary">
                {data.current.from_date} → {data.current.to_date}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-text-muted">vs</p>
              <p className="text-sm text-text-secondary">
                {data.previous.from_date} → {data.previous.to_date}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
