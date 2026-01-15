"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversionByProject } from "@/lib/api";
import { formatNumber, formatCurrency, cn } from "@/lib/utils";

interface ConversionBarChartProps {
  title: string;
  data: ConversionByProject[];
  isLoading?: boolean;
  showTop?: boolean; // true = top performers (green), false = bottom (red)
}

function getConversionColor(rate: number): string {
  if (rate >= 80) return "bg-status-success";
  if (rate >= 50) return "bg-status-pending";
  return "bg-status-failed";
}

function getConversionTextColor(rate: number): string {
  if (rate >= 80) return "text-status-success";
  if (rate >= 50) return "text-status-pending";
  return "text-status-failed";
}

export function ConversionBarChart({
  title,
  data,
  isLoading,
  showTop = true,
}: ConversionBarChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const maxCount = Math.max(...data.map((d) => d.total_count), 1);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">{title}</CardTitle>
          <span className={cn(
            "text-xs font-medium px-2 py-0.5 rounded",
            showTop ? "bg-status-success/20 text-status-success" : "bg-status-failed/20 text-status-failed"
          )}>
            {showTop ? "Top 5" : "Bottom 5"}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-[200px] text-text-muted">
            No data available
          </div>
        ) : (
          <div className="space-y-3">
            {data.map((project) => {
              const barWidth = (project.total_count / maxCount) * 100;
              const conversionColor = getConversionColor(project.conversion_rate);
              const textColor = getConversionTextColor(project.conversion_rate);
              
              return (
                <div key={project.project} className="space-y-1">
                  {/* Project info row */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-text-primary font-medium truncate max-w-[150px]">
                      {project.project}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-text-muted text-xs">
                        {formatNumber(project.total_count)} txns
                      </span>
                      <span className={cn("font-semibold tabular-nums", textColor)}>
                        {project.conversion_rate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
                    <div
                      className={cn("h-full rounded-full transition-all", conversionColor)}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  
                  {/* Secondary info */}
                  <div className="flex items-center justify-between text-xs text-text-muted">
                    <span>
                      {formatNumber(project.success_count)} success / {formatNumber(project.failed_count)} failed
                    </span>
                    <span>
                      Avg: {formatCurrency(project.avg_ticket, "INR")}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
