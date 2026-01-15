"use client";

import { useFilterStore } from "@/stores/filter-store";
import { cn } from "@/lib/utils";
import { Database, Layers } from "lucide-react";

const sources = [
  { id: null, label: "All Sources", icon: Layers },
  { id: "vima", label: "Vima", icon: Database, color: "text-blue-400" },
  { id: "payshack", label: "PayShack", icon: Database, color: "text-purple-400" },
] as const;

export function SourceTabs() {
  const { source, setSource } = useFilterStore();

  return (
    <div className="flex items-center gap-1 rounded-lg bg-background-secondary p-1 border border-border-primary">
      {sources.map((s) => {
        const isActive = source === s.id;
        const Icon = s.icon;
        
        return (
          <button
            key={s.id ?? "all"}
            onClick={() => setSource(s.id)}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all",
              isActive
                ? "bg-accent-primary text-white shadow-sm"
                : "text-text-secondary hover:text-text-primary hover:bg-background-tertiary"
            )}
          >
            <Icon className={cn("h-4 w-4", !isActive && s.color)} />
            <span>{s.label}</span>
          </button>
        );
      })}
    </div>
  );
}
