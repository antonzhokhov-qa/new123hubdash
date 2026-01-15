"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AmountBucketPoint } from "@/lib/api";
import { formatNumber, formatCurrency } from "@/lib/utils";

interface AmountHistogramProps {
  title: string;
  data?: AmountBucketPoint[];
  buckets?: string[];
  isLoading?: boolean;
}

// Aggregate by bucket (sum across all hours)
function aggregateByBucket(
  data: AmountBucketPoint[], 
  buckets: string[]
): Array<{ bucket: string; count: number; amount: number; bucketIndex: number }> {
  const bucketMap = new Map<number, { count: number; amount: number }>();

  // Initialize all buckets
  buckets.forEach((_, index) => {
    bucketMap.set(index, { count: 0, amount: 0 });
  });

  // Aggregate
  data.forEach((point) => {
    const existing = bucketMap.get(point.bucket_index);
    if (existing) {
      existing.count += point.count;
      existing.amount += point.total_amount;
    }
  });

  return buckets.map((bucket, index) => ({
    bucket,
    count: bucketMap.get(index)?.count || 0,
    amount: bucketMap.get(index)?.amount || 0,
    bucketIndex: index,
  }));
}

const COLORS = [
  "#3B82F6",
  "#6366F1",
  "#8B5CF6",
  "#A855F7",
  "#D946EF",
  "#EC4899",
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-background-primary border border-border-primary rounded-lg p-3 shadow-lg">
      <p className="text-sm font-medium text-text-primary mb-2">{label}</p>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <span className="text-text-secondary">Transactions:</span>
          <span className="font-medium text-text-primary">
            {formatNumber(data.count)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-text-secondary">Total Amount:</span>
          <span className="font-medium text-text-primary">
            {formatCurrency(data.amount, "INR")}
          </span>
        </div>
      </div>
    </div>
  );
};

export function AmountHistogram({
  title,
  data,
  buckets = ["₹0-100", "₹100-500", "₹500-1K", "₹1K-5K", "₹5K-10K", "₹10K+"],
  isLoading,
}: AmountHistogramProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-[300px]" />
        </CardContent>
      </Card>
    );
  }

  const chartData = data ? aggregateByBucket(data, buckets) : [];

  if (chartData.length === 0 || chartData.every(d => d.count === 0)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-text-muted">
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border-primary)"
              horizontal={true}
              vertical={false}
            />
            <XAxis
              type="number"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "var(--border-primary)" }}
              tickFormatter={(value) => formatNumber(value)}
            />
            <YAxis
              type="category"
              dataKey="bucket"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={70}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--background-tertiary)" }} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={32}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        
        {/* Summary stats */}
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-text-muted">Most Common</p>
            <p className="text-sm font-medium text-text-primary">
              {chartData.reduce((max, item) => 
                item.count > max.count ? item : max
              , chartData[0]).bucket}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-muted">Total Transactions</p>
            <p className="text-sm font-medium text-text-primary">
              {formatNumber(chartData.reduce((sum, item) => sum + item.count, 0))}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-muted">Total Volume</p>
            <p className="text-sm font-medium text-text-primary">
              {formatCurrency(chartData.reduce((sum, item) => sum + item.amount, 0), "INR")}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
