import { useQuery } from "@tanstack/react-query";
import { 
  api, 
  MetricsOverview, 
  MetricsByProject, 
  MetricsTrends, 
  HourlyDistribution, 
  AmountDistribution, 
  ConversionByProjectResponse,
  HeatmapResponse,
  PeriodComparisonResponse,
  MetricsByCountry,
  MerchantListResponse,
  MetricsBySource,
} from "@/lib/api";
import { mockMetricsOverview, mockMetricsByProject, mockMetricsTrends } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

interface MetricsParams {
  from_date?: string;
  to_date?: string;
  source?: string;
  project?: string;
}

// Transform backend response to frontend format
function transformMetricsOverview(backend: any): MetricsOverview {
  return {
    period: backend.period,
    total: {
      count: backend.total_count,
      amount: backend.total_amount,
      currency: backend.currency || "INR",
    },
    by_status: backend.by_status,
    by_source: backend.by_source,
    conversion_rate: backend.conversion_rate,
    avg_ticket: backend.avg_ticket,
    trends: {
      total_change: backend.count_change_percent || 0,
      success_change: 0,
      failed_change: 0,
    },
  };
}

function transformMetricsByProject(backend: any): MetricsByProject {
  return {
    period: backend.period,
    projects: backend.projects.map((p: any) => ({
      project: p.project,
      count: p.total_count,
      amount: p.total_amount,
      success_rate: p.conversion_rate,
    })),
  };
}

function transformMetricsTrends(backend: any): MetricsTrends {
  return {
    period: backend.period,
    granularity: backend.granularity as "hour" | "day" | "week",
    points: backend.data.map((d: any) => ({
      timestamp: d.timestamp,
      count: d.count,
      amount: d.amount,
      success_count: d.success_count,
      failed_count: d.failed_count,
    })),
  };
}

export function useMetricsOverview(params: MetricsParams) {
  return useQuery({
    queryKey: ["metrics", "overview", params],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 400));
        return { data: mockMetricsOverview };
      }
      const response = await api.getMetricsOverview(params);
      return { data: transformMetricsOverview(response) };
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}

export function useMetricsByProject(params: { from_date?: string; to_date?: string; source?: string }) {
  return useQuery({
    queryKey: ["metrics", "by-project", params],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 400));
        return { data: mockMetricsByProject };
      }
      const response = await api.getMetricsByProject(params);
      return { data: transformMetricsByProject(response) };
    },
    staleTime: 60_000,
  });
}

interface TrendsParams {
  from_date: string;
  to_date: string;
  granularity?: "minute" | "5min" | "15min" | "hour" | "day" | "week";
  source?: string;
  project?: string;
}

export function useMetricsTrends(params: TrendsParams) {
  return useQuery({
    queryKey: ["metrics", "trends", params],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 500));
        return { data: { ...mockMetricsTrends, granularity: params.granularity || "hour" } };
      }
      const response = await api.getMetricsTrends(params);
      return { data: transformMetricsTrends(response) };
    },
    staleTime: 5 * 60_000,
  });
}

interface HourlyDistParams {
  from_date?: string;
  to_date?: string;
  source?: string;
  project?: string;
}

export function useHourlyDistribution(params: HourlyDistParams) {
  return useQuery({
    queryKey: ["metrics", "hourly-distribution", params],
    queryFn: async () => {
      const response = await api.getHourlyDistribution(params);
      return { data: response };
    },
    staleTime: 5 * 60_000,
  });
}

export function useAmountDistribution(params: HourlyDistParams) {
  return useQuery({
    queryKey: ["metrics", "amount-distribution", params],
    queryFn: async () => {
      const response = await api.getAmountDistribution(params);
      return { data: response };
    },
    staleTime: 5 * 60_000,
  });
}

export function useConversionByProject(params: { from_date?: string; to_date?: string; source?: string }) {
  return useQuery({
    queryKey: ["metrics", "conversion-by-project", params],
    queryFn: async () => {
      const response = await api.getConversionByProject(params);
      return { data: response };
    },
    staleTime: 60_000,
  });
}

// New hooks for Analytics V2

interface HeatmapParams {
  dimension?: "hour_day" | "merchant_hour" | "merchant_day";
  metric?: "amount" | "count" | "conversion";
  from_date?: string;
  to_date?: string;
  source?: string;
}

export function useHeatmap(params: HeatmapParams) {
  return useQuery({
    queryKey: ["metrics", "heatmap", params],
    queryFn: async () => {
      const response = await api.getHeatmap(params);
      return { data: response };
    },
    staleTime: 5 * 60_000,
  });
}

interface ComparisonParams {
  comparison_type?: "day" | "week" | "month";
  from_date?: string;
  to_date?: string;
  source?: string;
  project?: string;
}

export function usePeriodComparison(params: ComparisonParams) {
  return useQuery({
    queryKey: ["metrics", "comparison", params],
    queryFn: async () => {
      const response = await api.getPeriodComparison(params);
      return { data: response };
    },
    staleTime: 60_000,
  });
}

export function useMetricsByCountry(params: { from_date?: string; to_date?: string; source?: string }) {
  return useQuery({
    queryKey: ["metrics", "by-country", params],
    queryFn: async () => {
      const response = await api.getMetricsByCountry(params);
      return { data: response };
    },
    staleTime: 5 * 60_000,
  });
}

interface MerchantParams {
  from_date?: string;
  to_date?: string;
  source?: string;
  search?: string;
  sort_by?: "total_amount" | "total_count" | "conversion_rate";
  order?: "asc" | "desc";
  page?: number;
  limit?: number;
}

export function useMerchants(params: MerchantParams) {
  return useQuery({
    queryKey: ["metrics", "merchants", params],
    queryFn: async () => {
      const response = await api.getMerchants(params);
      return { data: response };
    },
    staleTime: 60_000,
  });
}

export function useMetricsBySource(params: { from_date?: string; to_date?: string; granularity?: string }) {
  return useQuery({
    queryKey: ["metrics", "by-source", params],
    queryFn: async () => {
      const response = await api.getMetricsBySource(params);
      return { data: response };
    },
    staleTime: 60_000,
  });
}
