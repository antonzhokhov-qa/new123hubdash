"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { HeatmapResponse } from "@/lib/api";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";

interface HeatmapChartProps {
  title: string;
  data?: HeatmapResponse;
  isLoading?: boolean;
  metric?: "amount" | "count" | "conversion";
  height?: number;
}

function getColorIntensity(value: number, min: number, max: number): string {
  if (max === min) return "bg-accent-primary/20";
  
  const ratio = (value - min) / (max - min);
  
  if (ratio === 0) return "bg-background-tertiary";
  if (ratio < 0.2) return "bg-accent-primary/20";
  if (ratio < 0.4) return "bg-accent-primary/40";
  if (ratio < 0.6) return "bg-accent-primary/60";
  if (ratio < 0.8) return "bg-accent-primary/80";
  return "bg-accent-primary";
}

function formatValue(value: number, metric: string): string {
  if (metric === "amount") {
    return formatCurrency(value, "INR");
  }
  if (metric === "conversion") {
    return `${value.toFixed(1)}%`;
  }
  return formatNumber(value);
}

export function HeatmapChart({ 
  title, 
  data, 
  isLoading, 
  metric = "amount",
  height = 300,
}: HeatmapChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full" style={{ height }} />
        </CardContent>
      </Card>
    );
  }

  if (!data || data.cells.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div 
            className="flex items-center justify-center text-text-muted"
            style={{ height }}
          >
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Create a lookup map for cells
  const cellMap = new Map<string, typeof data.cells[0]>();
  data.cells.forEach(cell => {
    cellMap.set(`${cell.x}-${cell.y}`, cell);
  });

  const minValue = Number(data.min_value);
  const maxValue = Number(data.max_value);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className="p-1 text-left text-text-muted w-12"></th>
                {data.x_labels.map((label) => (
                  <th 
                    key={label} 
                    className="p-1 text-center text-text-muted font-normal min-w-[28px]"
                  >
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.y_labels.map((yLabel) => (
                <tr key={yLabel}>
                  <td className="p-1 text-text-muted font-medium whitespace-nowrap">
                    {yLabel}
                  </td>
                  {data.x_labels.map((xLabel) => {
                    const cell = cellMap.get(`${xLabel}-${yLabel}`);
                    const value = cell ? Number(cell.value) : 0;
                    const colorClass = getColorIntensity(value, minValue, maxValue);
                    
                    return (
                      <td key={`${xLabel}-${yLabel}`} className="p-0.5">
                        <div
                          className={cn(
                            "w-7 h-7 rounded-sm flex items-center justify-center",
                            "transition-all cursor-pointer hover:ring-2 hover:ring-accent-primary/50",
                            colorClass
                          )}
                          title={`${yLabel} ${xLabel}:00 - ${formatValue(value, metric)} (${cell?.count || 0} txns)`}
                        >
                          {value > 0 && (
                            <span className="text-[8px] text-white/80 font-medium">
                              {cell?.count || 0}
                            </span>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-end gap-2 mt-4 text-xs text-text-muted">
          <span>Less</span>
          <div className="flex gap-0.5">
            <div className="w-4 h-4 rounded-sm bg-background-tertiary" />
            <div className="w-4 h-4 rounded-sm bg-accent-primary/20" />
            <div className="w-4 h-4 rounded-sm bg-accent-primary/40" />
            <div className="w-4 h-4 rounded-sm bg-accent-primary/60" />
            <div className="w-4 h-4 rounded-sm bg-accent-primary/80" />
            <div className="w-4 h-4 rounded-sm bg-accent-primary" />
          </div>
          <span>More</span>
        </div>
      </CardContent>
    </Card>
  );
}
