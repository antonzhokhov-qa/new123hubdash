"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AmountDistribution, AmountBucketPoint, AmountHeatmapPoint } from "@/lib/api";
import { cn, formatNumber } from "@/lib/utils";

interface AmountHeatmapProps {
  title: string;
  data: AmountDistribution | null;
  isLoading?: boolean;
}

const HOURS = Array.from({ length: 24 }, (_, i) => i);

const BUCKET_COLORS = [
  "bg-blue-500",      // 0-100
  "bg-blue-400",      // 100-500
  "bg-purple-500",    // 500-1K
  "bg-purple-400",    // 1K-5K
  "bg-pink-500",      // 5K-10K
  "bg-pink-400",      // 10K+
];

function getIntensityClass(value: number, max: number): string {
  const intensity = max > 0 ? value / max : 0;
  if (intensity >= 0.8) return "opacity-100";
  if (intensity >= 0.6) return "opacity-80";
  if (intensity >= 0.4) return "opacity-60";
  if (intensity >= 0.2) return "opacity-40";
  if (intensity > 0) return "opacity-25";
  return "opacity-10";
}

export function AmountHeatmap({
  title,
  data,
  isLoading,
}: AmountHeatmapProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px] text-text-muted">
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Create lookup map and find max
  const dataMap = new Map<string, AmountHeatmapPoint>();
  let maxCount = 0;
  
  data.data.forEach((point) => {
    const key = `${point.bucket_index}-${point.hour}`;
    dataMap.set(key, point);
    if (point.count > maxCount) maxCount = point.count;
  });

  const buckets = data.buckets;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {/* Hour labels */}
            <div className="flex gap-[2px] mb-1 ml-20">
              {HOURS.filter((h) => h % 4 === 0).map((hour) => (
                <div
                  key={hour}
                  className="text-[10px] text-text-muted"
                  style={{ width: "48px", marginLeft: hour === 0 ? 0 : "0px" }}
                >
                  {hour.toString().padStart(2, "0")}:00
                </div>
              ))}
            </div>
            
            {/* Grid */}
            <div className="space-y-[2px]">
              {buckets.map((bucket, bucketIndex) => (
                <div key={bucket} className="flex items-center gap-[2px]">
                  {/* Bucket label */}
                  <div className="w-16 text-xs text-text-muted font-medium text-right pr-2">
                    {bucket}
                  </div>
                  
                  {/* Hour cells */}
                  {HOURS.map((hour) => {
                    const key = `${bucketIndex}-${hour}`;
                    const point = dataMap.get(key);
                    const count = point?.count || 0;
                    const intensityClass = getIntensityClass(count, maxCount);
                    const baseColor = BUCKET_COLORS[bucketIndex % BUCKET_COLORS.length];
                    
                    return (
                      <div
                        key={hour}
                        className={cn(
                          "w-5 h-5 rounded-sm transition-all cursor-pointer hover:ring-1 hover:ring-text-primary/50",
                          count > 0 ? baseColor : "bg-bg-tertiary",
                          count > 0 && intensityClass
                        )}
                        title={point 
                          ? `${bucket} at ${hour}:00 - ${formatNumber(count)} transactions`
                          : `${bucket} at ${hour}:00 - No data`
                        }
                      />
                    );
                  })}
                </div>
              ))}
            </div>
            
            {/* Legend */}
            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-2">
                {buckets.slice(0, 3).map((bucket, i) => (
                  <div key={bucket} className="flex items-center gap-1">
                    <div className={cn("w-3 h-3 rounded-sm", BUCKET_COLORS[i])} />
                    <span className="text-xs text-text-muted">{bucket}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">Less</span>
                <div className="flex gap-[2px]">
                  <div className="w-3 h-3 rounded-sm bg-accent-primary/10" />
                  <div className="w-3 h-3 rounded-sm bg-accent-primary/40" />
                  <div className="w-3 h-3 rounded-sm bg-accent-primary/70" />
                  <div className="w-3 h-3 rounded-sm bg-accent-primary" />
                </div>
                <span className="text-xs text-text-muted">More</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
