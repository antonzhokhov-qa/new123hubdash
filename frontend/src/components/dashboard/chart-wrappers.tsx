"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  LineChart,
  Line,
  ComposedChart,
  PieChart,
  Pie,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { useFilterStore } from "@/stores/filter-store";
import { 
  useMetricsTrends, 
  useHourlyDistribution, 
  useAmountDistribution,
  useConversionByProject,
  useHeatmap,
  usePeriodComparison,
  useMetricsByCountry,
  useMetricsByProject,
  useMetricsOverview,
} from "@/hooks/use-metrics";
import { FilterParams } from "./compact-filters";
import { formatNumber, formatCurrency, cn } from "@/lib/utils";
import { format } from "date-fns";
import { ArrowUp, ArrowDown, Minus, Globe } from "lucide-react";

// ============ Trend Chart Content ============
interface TrendChartContentProps {
  params: FilterParams;
  height?: number;
}

export function TrendChartContent({ params, height = 220 }: TrendChartContentProps) {
  const { data, isLoading } = useMetricsTrends({
    from_date: params.from_date || "",
    to_date: params.to_date || "",
    source: params.source,
    granularity: params.granularity as any || "hour",
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const chartData = (data?.data?.points || []).map((item: any) => ({
    ...item,
    time: format(new Date(item.timestamp), "HH:mm"),
    date: format(new Date(item.timestamp), "MMM dd"),
  }));

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data available
      </div>
    );
  }

  const dataKey = params.metric === "amount" ? "amount" : "count";

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
        <XAxis
          dataKey="time"
          stroke="#71717A"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#71717A"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => formatNumber(value)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1A1A24",
            border: "1px solid #27272A",
            borderRadius: "8px",
          }}
          labelStyle={{ color: "#FAFAFA" }}
          formatter={(value: number) => [formatNumber(value), ""]}
        />
        <Area
          type="monotone"
          dataKey="success_count"
          stackId="1"
          stroke="#22C55E"
          fill="url(#colorSuccess)"
          name="Success"
        />
        <Area
          type="monotone"
          dataKey="failed_count"
          stackId="1"
          stroke="#EF4444"
          fill="url(#colorFailed)"
          name="Failed"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ============ Heatmap Chart Content ============
interface HeatmapChartContentProps {
  params: FilterParams;
  height?: number;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export function HeatmapChartContent({ params, height = 220 }: HeatmapChartContentProps) {
  const { data, isLoading } = useHeatmap({
    dimension: "hour_day",
    metric: (params.metric as "amount" | "count" | "conversion") || "amount",
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const heatmapData = data?.data;
  if (!heatmapData || heatmapData.cells.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data available
      </div>
    );
  }

  type CellType = { x: string; y: string; value: number; count?: number };
  const cellMap = new Map<string, CellType>();
  heatmapData.cells.forEach((cell: CellType) => {
    cellMap.set(`${cell.x}-${cell.y}`, cell);
  });

  const minValue = Number(heatmapData.min_value);
  const maxValue = Number(heatmapData.max_value);

  const getColorIntensity = (value: number): string => {
    if (maxValue === minValue) return "bg-accent-primary/20";
    const ratio = (value - minValue) / (maxValue - minValue);
    if (ratio === 0) return "bg-background-tertiary";
    if (ratio < 0.2) return "bg-accent-primary/20";
    if (ratio < 0.4) return "bg-accent-primary/40";
    if (ratio < 0.6) return "bg-accent-primary/60";
    if (ratio < 0.8) return "bg-accent-primary/80";
    return "bg-accent-primary";
  };

  return (
    <div className="overflow-x-auto" style={{ maxHeight: height }}>
      <div className="min-w-[500px]">
        <div className="flex gap-[2px] mb-1 ml-10">
          {HOURS.filter((h) => h % 4 === 0).map((hour) => (
            <div key={hour} className="text-[9px] text-text-muted" style={{ width: "48px" }}>
              {hour.toString().padStart(2, "0")}:00
            </div>
          ))}
        </div>
        <div className="space-y-[2px]">
          {DAYS.map((day) => (
            <div key={day} className="flex items-center gap-[2px]">
              <div className="w-8 text-[10px] text-text-muted font-medium">{day}</div>
              {HOURS.map((hour) => {
                const cell = cellMap.get(`${hour}-${day}`);
                const value = cell ? Number(cell.value) : 0;
                return (
                  <div
                    key={hour}
                    className={cn(
                      "w-4 h-4 rounded-sm cursor-pointer hover:ring-1 hover:ring-text-primary/50 transition-all",
                      getColorIntensity(value)
                    )}
                    title={`${day} ${hour}:00 - ${cell?.count || 0} txns`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ Hourly Conversion Chart Content ============
interface HourlyConversionContentProps {
  params: FilterParams;
  height?: number;
}

export function HourlyConversionContent({ params, height = 220 }: HourlyConversionContentProps) {
  const { data, isLoading } = useHourlyDistribution({
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const hourlyData = data?.data?.data || [];
  
  // Aggregate by hour
  const hourMap = new Map<number, { count: number; success: number }>();
  for (let h = 0; h < 24; h++) {
    hourMap.set(h, { count: 0, success: 0 });
  }
  hourlyData.forEach((point: any) => {
    const existing = hourMap.get(point.hour)!;
    existing.count += point.count;
    existing.success += point.success_count;
  });

  const chartData = Array.from(hourMap.entries()).map(([hour, stats]) => ({
    hour: `${hour.toString().padStart(2, "0")}:00`,
    count: stats.count,
    conversion: stats.count > 0 ? Math.round((stats.success / stats.count) * 100) : 0,
  }));

  if (chartData.every(d => d.count === 0)) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
        <XAxis dataKey="hour" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} interval={3} />
        <YAxis yAxisId="left" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} />
        <YAxis yAxisId="right" orientation="right" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
        <Tooltip
          contentStyle={{ backgroundColor: "#1A1A24", border: "1px solid #27272A", borderRadius: "8px" }}
          formatter={(value: number, name: string) => [name === "conversion" ? `${value}%` : formatNumber(value), name]}
        />
        <Bar yAxisId="left" dataKey="count" fill="#6366F1" opacity={0.3} radius={[4, 4, 0, 0]} />
        <Line yAxisId="right" type="monotone" dataKey="conversion" stroke="#22C55E" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ============ Amount Distribution Content ============
interface AmountDistributionContentProps {
  params: FilterParams;
  height?: number;
}

const COLORS = ["#3B82F6", "#6366F1", "#8B5CF6", "#A855F7", "#D946EF", "#EC4899"];

export function AmountDistributionContent({ params, height = 220 }: AmountDistributionContentProps) {
  const { data, isLoading } = useAmountDistribution({
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const distData = data?.data;
  if (!distData || !distData.data || distData.data.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data available
      </div>
    );
  }

  // Aggregate by bucket
  const bucketMap = new Map<number, number>();
  distData.buckets.forEach((_: string, i: number) => bucketMap.set(i, 0));
  distData.data.forEach((point: any) => {
    const existing = bucketMap.get(point.bucket_index) || 0;
    bucketMap.set(point.bucket_index, existing + point.count);
  });

  const chartData = distData.buckets.map((bucket: string, i: number) => ({
    bucket,
    count: bucketMap.get(i) || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" horizontal={true} vertical={false} />
        <XAxis type="number" stroke="#71717A" fontSize={10} tickLine={false} tickFormatter={(v) => formatNumber(v)} />
        <YAxis type="category" dataKey="bucket" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} width={60} />
        <Tooltip
          contentStyle={{ backgroundColor: "#1A1A24", border: "1px solid #27272A", borderRadius: "8px" }}
          formatter={(value: number) => [formatNumber(value), "Transactions"]}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={24}>
          {chartData.map((_: any, i: number) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ============ Conversion Bar Chart Content ============
interface ConversionBarContentProps {
  params: FilterParams;
  showTop?: boolean;
  height?: number;
}

export function ConversionBarContent({ params, showTop = true, height = 220 }: ConversionBarContentProps) {
  const { data, isLoading } = useConversionByProject({
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const limit = params.limit || 5;
  const projects = showTop 
    ? (data?.data?.top_5 || []).slice(0, limit)
    : (data?.data?.bottom_5 || []).slice(0, limit);

  if (projects.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data available
      </div>
    );
  }

  const getColor = (rate: number) => {
    if (rate >= 70) return "bg-status-success";
    if (rate >= 40) return "bg-status-pending";
    return "bg-status-failed";
  };

  return (
    <div className="space-y-2" style={{ maxHeight: height, overflowY: "auto" }}>
      {projects.map((p: any, i: number) => (
        <div key={p.project} className="flex items-center gap-3">
          <span className="text-xs text-text-muted w-4">#{i + 1}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-text-primary truncate">{p.project}</span>
              <span className={cn(
                "text-xs font-medium px-1.5 py-0.5 rounded",
                p.conversion_rate >= 70 ? "text-status-success bg-status-success/10" :
                p.conversion_rate >= 40 ? "text-status-pending bg-status-pending/10" :
                "text-status-failed bg-status-failed/10"
              )}>
                {p.conversion_rate.toFixed(1)}%
              </span>
            </div>
            <div className="h-1.5 bg-background-tertiary rounded-full overflow-hidden">
              <div className={cn("h-full rounded-full", getColor(p.conversion_rate))} style={{ width: `${Math.min(p.conversion_rate, 100)}%` }} />
            </div>
            <div className="text-[10px] text-text-muted mt-0.5">{formatNumber(p.total_count)} txns</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============ Period Comparison Content ============
interface PeriodComparisonContentProps {
  params: FilterParams;
  height?: number;
}

export function PeriodComparisonContent({ params, height = 220 }: PeriodComparisonContentProps) {
  const { displayCurrency } = useFilterStore();
  const comparisonType = params.period === "today" || params.period === "yesterday" ? "day" : "week";
  
  const { data, isLoading } = usePeriodComparison({
    comparison_type: comparisonType,
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const comparison = data?.data;
  if (!comparison) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data available
      </div>
    );
  }

  // Use USD or INR based on selected currency
  const volumeValue = displayCurrency === "USD" && comparison.current.total_amount_usd
    ? formatCurrency(comparison.current.total_amount_usd, "USD")
    : formatCurrency(comparison.current.total_amount, "INR");
    
  const avgTicketValue = displayCurrency === "USD" && comparison.current.avg_ticket_usd
    ? formatCurrency(comparison.current.avg_ticket_usd, "USD")
    : formatCurrency(comparison.current.avg_ticket, "INR");

  const metrics = [
    { label: "Volume", current: volumeValue, change: comparison.comparison.amount_change_percent },
    { label: "Transactions", current: formatNumber(comparison.current.total_count), change: comparison.comparison.count_change_percent },
    { label: "Conversion", current: `${comparison.current.conversion_rate.toFixed(1)}%`, change: comparison.comparison.conversion_change },
    { label: "Avg Ticket", current: avgTicketValue, change: comparison.comparison.avg_ticket_change_percent },
  ];

  return (
    <div className="space-y-2" style={{ maxHeight: height, overflowY: "auto" }}>
      {metrics.map((m) => (
        <div key={m.label} className="flex items-center justify-between py-1.5 border-b border-border-primary/50 last:border-0">
          <span className="text-xs text-text-muted">{m.label}</span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-text-primary">{m.current}</span>
            <div className={cn(
              "flex items-center gap-0.5 text-xs",
              m.change > 0 ? "text-status-success" : m.change < 0 ? "text-status-failed" : "text-text-muted"
            )}>
              {m.change > 0 ? <ArrowUp className="h-3 w-3" /> : m.change < 0 ? <ArrowDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
              <span>{Math.abs(m.change).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============ Geo Chart Content ============
interface GeoChartContentProps {
  params: FilterParams;
  height?: number;
}

export function GeoChartContent({ params, height = 220 }: GeoChartContentProps) {
  const { data, isLoading } = useMetricsByCountry({
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const countries = data?.data?.countries || [];
  if (countries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-text-muted" style={{ height }}>
        <Globe className="h-8 w-8 mb-2 opacity-30" />
        <span>No geo data</span>
      </div>
    );
  }

  const COUNTRY_FLAGS: Record<string, string> = {
    IN: "🇮🇳", US: "🇺🇸", GB: "🇬🇧", AE: "🇦🇪", SG: "🇸🇬", BD: "🇧🇩", XX: "🌍",
  };

  return (
    <div className="space-y-2" style={{ maxHeight: height, overflowY: "auto" }}>
      {countries.slice(0, 5).map((c: any) => (
        <div key={c.country} className="flex items-center gap-3 p-2 rounded-lg hover:bg-background-secondary">
          <span className="text-xl">{COUNTRY_FLAGS[c.country] || COUNTRY_FLAGS.XX}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-text-primary">{c.country_name}</span>
              <span className="text-xs text-text-muted">{c.percentage_of_total.toFixed(1)}%</span>
            </div>
            <div className="h-1 bg-background-tertiary rounded-full mt-1">
              <div className="h-full bg-accent-primary rounded-full" style={{ width: `${Math.min(c.percentage_of_total, 100)}%` }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============ Donut Chart Content (Status/Source) ============
interface DonutChartContentProps {
  params: FilterParams;
  type: "status" | "source";
  height?: number;
}

export function DonutChartContent({ params, type, height = 180 }: DonutChartContentProps) {
  const { data, isLoading } = useMetricsOverview({
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const metrics = data?.data;
  if (!metrics) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data
      </div>
    );
  }

  const chartData = type === "status"
    ? [
        { name: "Success", value: metrics.by_status.success.count, color: "#22C55E" },
        { name: "Failed", value: metrics.by_status.failed.count, color: "#EF4444" },
        { name: "Pending", value: metrics.by_status.pending?.count || 0, color: "#F59E0B" },
      ]
    : [
        { name: "Vima", value: metrics.by_source?.vima?.count || 0, color: "#3B82F6" },
        { name: "PayShack", value: metrics.by_source?.payshack?.count || 0, color: "#A855F7" },
      ];

  const total = chartData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="flex items-center gap-4">
      <ResponsiveContainer width={height} height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={height * 0.25}
            outerRadius={height * 0.4}
            dataKey="value"
            stroke="none"
          >
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="space-y-1.5">
        {chartData.map((d) => (
          <div key={d.name} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
            <span className="text-xs text-text-muted">{d.name}</span>
            <span className="text-xs font-medium text-text-primary">{formatNumber(d.value)}</span>
          </div>
        ))}
        <div className="pt-1 border-t border-border-primary/50">
          <span className="text-xs text-text-muted">Total: </span>
          <span className="text-xs font-medium text-text-primary">{formatNumber(total)}</span>
        </div>
      </div>
    </div>
  );
}

// ============ Project Bar Chart Content ============
interface ProjectBarContentProps {
  params: FilterParams;
  height?: number;
}

export function ProjectBarContent({ params, height = 220 }: ProjectBarContentProps) {
  const { data, isLoading } = useMetricsByProject({
    from_date: params.from_date,
    to_date: params.to_date,
    source: params.source,
  });

  if (isLoading) {
    return <Skeleton className="w-full" style={{ height }} />;
  }

  const projects = data?.data?.projects || [];
  if (projects.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted" style={{ height }}>
        No data
      </div>
    );
  }

  const chartData = projects.slice(0, params.limit || 6).map((p: any) => ({
    name: p.project,
    value: p.count,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" horizontal={true} vertical={false} />
        <XAxis type="number" stroke="#71717A" fontSize={10} tickLine={false} tickFormatter={(v) => formatNumber(v)} />
        <YAxis type="category" dataKey="name" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} width={80} />
        <Tooltip
          contentStyle={{ backgroundColor: "#1A1A24", border: "1px solid #27272A", borderRadius: "8px" }}
          formatter={(value: number) => [formatNumber(value), "Transactions"]}
        />
        <Bar dataKey="value" fill="#6366F1" radius={[0, 4, 4, 0]} maxBarSize={20} />
      </BarChart>
    </ResponsiveContainer>
  );
}
