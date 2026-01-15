"use client";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { useEffect, useState } from "react";

interface KPICardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: number;
  icon?: LucideIcon;
  color?: "default" | "success" | "failed" | "pending";
  isLoading?: boolean;
  className?: string;
}

export function KPICard({
  label,
  value,
  subtext,
  trend,
  icon: Icon,
  color = "default",
  isLoading,
  className,
}: KPICardProps) {
  const [displayValue, setDisplayValue] = useState<string | number>(0);

  // Animate number count-up
  useEffect(() => {
    if (isLoading) return;
    
    if (typeof value === "number") {
      const duration = 500;
      const steps = 20;
      const increment = value / steps;
      let current = 0;
      let step = 0;

      const timer = setInterval(() => {
        step++;
        current += increment;
        if (step >= steps) {
          setDisplayValue(value);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.round(current));
        }
      }, duration / steps);

      return () => clearInterval(timer);
    } else {
      setDisplayValue(value);
    }
  }, [value, isLoading]);

  const colorClasses = {
    default: "text-accent-primary",
    success: "text-status-success",
    failed: "text-status-failed",
    pending: "text-status-pending",
  };

  const bgClasses = {
    default: "bg-accent-glow",
    success: "bg-status-success-bg",
    failed: "bg-status-failed-bg",
    pending: "bg-status-pending-bg",
  };

  if (isLoading) {
    return (
      <Card className={cn("p-6", className)}>
        <div className="space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        "p-6 card-hover group",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm text-text-muted">{label}</p>
          <p className={cn("text-2xl font-bold number-animate", colorClasses[color])}>
            {displayValue}
          </p>
          {subtext && (
            <p className="text-sm text-text-secondary">{subtext}</p>
          )}
        </div>

        {Icon && (
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-lg transition-colors",
              bgClasses[color]
            )}
          >
            <Icon className={cn("h-5 w-5", colorClasses[color])} />
          </div>
        )}
      </div>

      {trend !== undefined && (
        <div className="mt-3 flex items-center gap-1">
          {trend >= 0 ? (
            <TrendingUp className="h-4 w-4 text-status-success" />
          ) : (
            <TrendingDown className="h-4 w-4 text-status-failed" />
          )}
          <span
            className={cn(
              "text-sm font-medium",
              trend >= 0 ? "text-status-success" : "text-status-failed"
            )}
          >
            {trend >= 0 ? "+" : ""}
            {trend.toFixed(1)}%
          </span>
          <span className="text-sm text-text-muted">vs previous</span>
        </div>
      )}
    </Card>
  );
}
