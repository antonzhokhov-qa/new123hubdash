"use client";

import { Database, Layers, Clock, BarChart3, Hash, Calendar } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Common compact select wrapper
interface CompactSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  icon?: React.ReactNode;
  className?: string;
}

function CompactSelect({
  value,
  onValueChange,
  options,
  placeholder,
  icon,
  className,
}: CompactSelectProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger
        className={cn(
          "h-7 min-w-[90px] text-xs px-2 gap-1 border-border-primary/50 bg-background-tertiary/50",
          className
        )}
      >
        {icon && <span className="text-text-muted">{icon}</span>}
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value} className="text-xs">
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

// Source Select (Vima/PayShack/All)
interface SourceSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function SourceSelect({ value, onValueChange, className }: SourceSelectProps) {
  const options = [
    { value: "all", label: "All Sources" },
    { value: "vima", label: "Vima" },
    { value: "payshack", label: "PayShack" },
  ];

  return (
    <CompactSelect
      value={value}
      onValueChange={onValueChange}
      options={options}
      placeholder="Source"
      icon={<Database className="h-3 w-3" />}
      className={className}
    />
  );
}

// Period Select (Today/Yesterday/7d/30d)
interface PeriodSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function PeriodSelect({ value, onValueChange, className }: PeriodSelectProps) {
  const options = [
    { value: "today", label: "Today" },
    { value: "yesterday", label: "Yesterday" },
    { value: "7d", label: "7 Days" },
    { value: "30d", label: "30 Days" },
  ];

  return (
    <CompactSelect
      value={value}
      onValueChange={onValueChange}
      options={options}
      placeholder="Period"
      icon={<Calendar className="h-3 w-3" />}
      className={className}
    />
  );
}

// Granularity Select (15min/hour/day)
interface GranularitySelectProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function GranularitySelect({ value, onValueChange, className }: GranularitySelectProps) {
  const options = [
    { value: "5min", label: "5 min" },
    { value: "15min", label: "15 min" },
    { value: "hour", label: "Hour" },
    { value: "day", label: "Day" },
  ];

  return (
    <CompactSelect
      value={value}
      onValueChange={onValueChange}
      options={options}
      placeholder="Granularity"
      icon={<Clock className="h-3 w-3" />}
      className={className}
    />
  );
}

// Metric Select (count/amount/conversion)
interface MetricSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options?: { value: string; label: string }[];
  className?: string;
}

export function MetricSelect({ 
  value, 
  onValueChange, 
  options,
  className 
}: MetricSelectProps) {
  const defaultOptions = [
    { value: "count", label: "Count" },
    { value: "amount", label: "Amount" },
    { value: "conversion", label: "Conversion" },
  ];

  return (
    <CompactSelect
      value={value}
      onValueChange={onValueChange}
      options={options || defaultOptions}
      placeholder="Metric"
      icon={<BarChart3 className="h-3 w-3" />}
      className={className}
    />
  );
}

// Limit Select (5/10/15/20)
interface LimitSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function LimitSelect({ value, onValueChange, className }: LimitSelectProps) {
  const options = [
    { value: "5", label: "Top 5" },
    { value: "10", label: "Top 10" },
    { value: "15", label: "Top 15" },
    { value: "20", label: "Top 20" },
  ];

  return (
    <CompactSelect
      value={value}
      onValueChange={onValueChange}
      options={options}
      placeholder="Limit"
      icon={<Hash className="h-3 w-3" />}
      className={className}
    />
  );
}

// Export types for filter params
export interface FilterParams {
  source?: string;
  period?: string;
  granularity?: string;
  metric?: string;
  limit?: number;
  from_date?: string;
  to_date?: string;
}

// Helper to convert period to date params
export function periodToDateParams(period: string): { from_date: string; to_date: string } {
  const today = new Date();
  const formatDate = (d: Date) => d.toISOString().split("T")[0];
  
  const to_date = formatDate(today);
  let from_date: string;

  switch (period) {
    case "today":
      from_date = to_date;
      break;
    case "yesterday":
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      from_date = formatDate(yesterday);
      return { from_date, to_date: from_date };
    case "7d":
      const week = new Date(today);
      week.setDate(week.getDate() - 6);
      from_date = formatDate(week);
      break;
    case "30d":
      const month = new Date(today);
      month.setDate(month.getDate() - 29);
      from_date = formatDate(month);
      break;
    default:
      from_date = to_date;
  }

  return { from_date, to_date };
}
