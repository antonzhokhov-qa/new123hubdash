"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CountryMetrics } from "@/lib/api";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";
import { Globe } from "lucide-react";

interface GeoChartProps {
  title: string;
  data?: CountryMetrics[];
  totalAmount?: number;
  isLoading?: boolean;
}

// Country flag emojis
const COUNTRY_FLAGS: Record<string, string> = {
  IN: "🇮🇳",
  US: "🇺🇸",
  GB: "🇬🇧",
  AE: "🇦🇪",
  SG: "🇸🇬",
  BD: "🇧🇩",
  NP: "🇳🇵",
  PK: "🇵🇰",
  LK: "🇱🇰",
  XX: "🌍",
};

// Color gradient based on percentage
function getProgressColor(percentage: number): string {
  if (percentage >= 50) return "bg-accent-primary";
  if (percentage >= 25) return "bg-accent-primary/80";
  if (percentage >= 10) return "bg-accent-primary/60";
  if (percentage >= 5) return "bg-accent-primary/40";
  return "bg-accent-primary/20";
}

function getConversionColor(rate: number): string {
  if (rate >= 90) return "text-status-success";
  if (rate >= 70) return "text-status-pending";
  return "text-status-failed";
}

export function GeoChart({
  title,
  data,
  totalAmount,
  isLoading,
}: GeoChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[300px] text-text-muted">
            <Globe className="h-12 w-12 mb-4 opacity-30" />
            <p>No geo data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sort by amount descending
  const sortedData = [...data].sort((a, b) => b.total_amount - a.total_amount);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">{title}</CardTitle>
          {totalAmount && (
            <span className="text-sm text-text-muted">
              Total: {formatCurrency(totalAmount, "INR")}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedData.map((country, index) => (
            <div
              key={country.country}
              className={cn(
                "p-3 rounded-lg transition-colors",
                "hover:bg-background-secondary",
                index === 0 && "bg-background-secondary"
              )}
            >
              {/* Country header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {COUNTRY_FLAGS[country.country] || COUNTRY_FLAGS.XX}
                  </span>
                  <div>
                    <p className="font-medium text-text-primary">
                      {country.country_name}
                    </p>
                    <p className="text-xs text-text-muted">
                      {formatNumber(country.total_count)} transactions
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-text-primary">
                    {formatCurrency(country.total_amount, "INR")}
                  </p>
                  <p className="text-xs text-text-muted">
                    {country.percentage_of_total.toFixed(1)}% of total
                  </p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-background-tertiary rounded-full overflow-hidden mb-2">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    getProgressColor(country.percentage_of_total)
                  )}
                  style={{ width: `${Math.min(country.percentage_of_total, 100)}%` }}
                />
              </div>

              {/* Stats row */}
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-4">
                  <span className="text-text-muted">
                    <span className="text-status-success">✓</span>{" "}
                    {formatNumber(country.success_count)} success
                  </span>
                  <span className="text-text-muted">
                    <span className="text-status-failed">✗</span>{" "}
                    {formatNumber(country.failed_count)} failed
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-text-muted">Conversion:</span>
                  <span className={cn("font-medium", getConversionColor(country.conversion_rate))}>
                    {country.conversion_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-4 pt-4 border-t border-border-primary">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-text-muted">Countries</p>
              <p className="text-lg font-semibold text-text-primary">
                {data.length}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Top Country</p>
              <p className="text-lg font-semibold text-text-primary">
                {sortedData[0]?.country_name || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Avg Conversion</p>
              <p className="text-lg font-semibold text-text-primary">
                {(
                  data.reduce((sum, c) => sum + c.conversion_rate, 0) / data.length
                ).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
