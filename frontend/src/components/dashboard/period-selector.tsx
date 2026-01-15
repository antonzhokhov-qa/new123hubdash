"use client";

import { useFilterStore, DateRangePreset } from "@/stores/filter-store";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Calendar } from "lucide-react";

const presets: { value: DateRangePreset; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "yesterday", label: "Yesterday" },
  { value: "last7days", label: "7 Days" },
  { value: "last30days", label: "30 Days" },
];

interface PeriodSelectorProps {
  className?: string;
}

export function PeriodSelector({ className }: PeriodSelectorProps) {
  const { dateRangePreset, setDateRangePreset } = useFilterStore();

  return (
    <div className={cn("flex items-center gap-1 rounded-lg bg-background-secondary p-1", className)}>
      {presets.map((preset) => (
        <Button
          key={preset.value}
          variant="ghost"
          size="sm"
          onClick={() => setDateRangePreset(preset.value)}
          className={cn(
            "h-8 px-3 text-xs",
            dateRangePreset === preset.value
              ? "bg-background-tertiary text-text-primary"
              : "text-text-muted hover:text-text-secondary"
          )}
        >
          {preset.label}
        </Button>
      ))}
      <Button
        variant="ghost"
        size="icon"
        className={cn(
          "h-8 w-8",
          dateRangePreset === "custom"
            ? "bg-background-tertiary text-text-primary"
            : "text-text-muted hover:text-text-secondary"
        )}
      >
        <Calendar className="h-4 w-4" />
      </Button>
    </div>
  );
}
