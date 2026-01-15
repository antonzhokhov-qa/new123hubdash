"use client";

import { useState, ReactNode, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useFilterStore } from "@/stores/filter-store";
import {
  SourceSelect,
  PeriodSelect,
  GranularitySelect,
  MetricSelect,
  LimitSelect,
  FilterParams,
  periodToDateParams,
} from "./compact-filters";

export interface ChartCardFilters {
  source?: boolean;
  period?: boolean;
  granularity?: boolean;
  metric?: boolean;
  limit?: boolean;
}

export interface ChartCardProps {
  title: string;
  children: (params: FilterParams) => ReactNode;
  filters?: ChartCardFilters;
  defaultGranularity?: string;
  defaultMetric?: string;
  defaultLimit?: number;
  metricOptions?: { value: string; label: string }[];
  className?: string;
  minWidth?: string;
}

export function ChartCard({
  title,
  children,
  filters = {},
  defaultGranularity = "hour",
  defaultMetric = "count",
  defaultLimit = 5,
  metricOptions,
  className,
  minWidth = "400px",
}: ChartCardProps) {
  // Get global filter values as defaults
  const globalStore = useFilterStore();
  const globalDateParams = globalStore.getDateParams();
  const globalSource = globalStore.source;
  const globalPeriod = globalStore.dateRangePreset;

  // Local filter state - initialized from global
  const [localSource, setLocalSource] = useState<string>(globalSource || "all");
  const [localPeriod, setLocalPeriod] = useState<string>(
    globalPeriod === "last7days" ? "7d" : 
    globalPeriod === "last30days" ? "30d" : 
    globalPeriod
  );
  const [localGranularity, setLocalGranularity] = useState<string>(defaultGranularity);
  const [localMetric, setLocalMetric] = useState<string>(defaultMetric);
  const [localLimit, setLocalLimit] = useState<string>(String(defaultLimit));

  // Sync with global filters when they change
  useEffect(() => {
    if (!filters.source) return;
    setLocalSource(globalSource || "all");
  }, [globalSource, filters.source]);

  useEffect(() => {
    if (!filters.period) return;
    const mapped = globalPeriod === "last7days" ? "7d" : 
                   globalPeriod === "last30days" ? "30d" : 
                   globalPeriod;
    setLocalPeriod(mapped);
  }, [globalPeriod, filters.period]);

  // Build params for children
  const buildParams = (): FilterParams => {
    const params: FilterParams = {};

    // Source
    if (filters.source) {
      params.source = localSource === "all" ? undefined : localSource;
    } else if (globalSource) {
      params.source = globalSource;
    }

    // Period / Date params
    if (filters.period) {
      const { from_date, to_date } = periodToDateParams(localPeriod);
      params.from_date = from_date;
      params.to_date = to_date;
      params.period = localPeriod;
    } else {
      params.from_date = globalDateParams.from_date;
      params.to_date = globalDateParams.to_date;
    }

    // Granularity
    if (filters.granularity) {
      params.granularity = localGranularity;
    }

    // Metric
    if (filters.metric) {
      params.metric = localMetric;
    }

    // Limit
    if (filters.limit) {
      params.limit = parseInt(localLimit, 10);
    }

    return params;
  };

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <Card 
      className={className}
      style={{ minWidth }}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <CardTitle className="text-base font-medium whitespace-nowrap">
            {title}
          </CardTitle>
          
          {hasFilters && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {filters.source && (
                <SourceSelect
                  value={localSource}
                  onValueChange={setLocalSource}
                />
              )}
              {filters.period && (
                <PeriodSelect
                  value={localPeriod}
                  onValueChange={setLocalPeriod}
                />
              )}
              {filters.granularity && (
                <GranularitySelect
                  value={localGranularity}
                  onValueChange={setLocalGranularity}
                />
              )}
              {filters.metric && (
                <MetricSelect
                  value={localMetric}
                  onValueChange={setLocalMetric}
                  options={metricOptions}
                />
              )}
              {filters.limit && (
                <LimitSelect
                  value={localLimit}
                  onValueChange={setLocalLimit}
                />
              )}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {children(buildParams())}
      </CardContent>
    </Card>
  );
}
