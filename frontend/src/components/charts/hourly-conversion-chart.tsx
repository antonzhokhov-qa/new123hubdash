"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ComposedChart,
  Bar,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { HourlyDistributionPoint } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

interface HourlyConversionChartProps {
  title: string;
  data?: HourlyDistributionPoint[];
  isLoading?: boolean;
}

// Aggregate data by hour (sum across all days)
function aggregateByHour(data: HourlyDistributionPoint[]): Array<{
  hour: string;
  count: number;
  success_count: number;
  failed_count: number;
  conversion_rate: number;
}> {
  const hourMap = new Map<number, {
    count: number;
    success_count: number;
    failed_count: number;
  }>();

  // Initialize all hours
  for (let h = 0; h < 24; h++) {
    hourMap.set(h, { count: 0, success_count: 0, failed_count: 0 });
  }

  // Aggregate
  data.forEach((point) => {
    const existing = hourMap.get(point.hour)!;
    existing.count += point.count;
    existing.success_count += point.success_count;
    existing.failed_count += point.failed_count;
  });

  return Array.from(hourMap.entries()).map(([hour, stats]) => ({
    hour: `${hour.toString().padStart(2, "0")}:00`,
    count: stats.count,
    success_count: stats.success_count,
    failed_count: stats.failed_count,
    conversion_rate: stats.count > 0 
      ? Math.round((stats.success_count / stats.count) * 1000) / 10 
      : 0,
  }));
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-background-primary border border-border-primary rounded-lg p-3 shadow-lg">
      <p className="text-sm font-medium text-text-primary mb-2">{label}</p>
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-text-secondary">{entry.name}:</span>
          <span className="font-medium text-text-primary">
            {entry.name === "Conversion %" 
              ? `${entry.value}%`
              : formatNumber(entry.value)
            }
          </span>
        </div>
      ))}
    </div>
  );
};

export function HourlyConversionChart({
  title,
  data,
  isLoading,
}: HourlyConversionChartProps) {
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

  const chartData = data ? aggregateByHour(data) : [];

  if (chartData.length === 0) {
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
          <ComposedChart data={chartData}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="var(--border-primary)" 
              vertical={false}
            />
            <XAxis
              dataKey="hour"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "var(--border-primary)" }}
              interval={2}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => formatNumber(value)}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}%`}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: "20px" }}
              formatter={(value) => (
                <span className="text-text-secondary text-sm">{value}</span>
              )}
            />
            <Bar
              yAxisId="left"
              dataKey="count"
              name="Transactions"
              fill="var(--accent-primary)"
              opacity={0.3}
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="conversion_rate"
              name="Conversion %"
              stroke="#22C55E"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: "#22C55E" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
