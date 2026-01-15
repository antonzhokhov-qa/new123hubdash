"use client";

import { useFilterStore } from "@/stores/filter-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X, Download } from "lucide-react";
import { PeriodSelector } from "@/components/dashboard/period-selector";

interface FilterPanelProps {
  onExport?: (format: "csv" | "xlsx") => void;
  isExporting?: boolean;
}

export function FilterPanel({ onExport, isExporting }: FilterPanelProps) {
  const {
    source,
    project,
    status,
    search,
    setSource,
    setProject,
    setStatus,
    setSearch,
    resetFilters,
  } = useFilterStore();

  const hasFilters = source || project || status || search;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
          <Input
            placeholder="Search by ID, email, phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Source filter */}
        <Select value={source || "all"} onValueChange={(v) => setSource(v === "all" ? null : v)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sources</SelectItem>
            <SelectItem value="vima">Vima</SelectItem>
            <SelectItem value="payshack">PayShack</SelectItem>
          </SelectContent>
        </Select>

        {/* Project filter */}
        <Select value={project || "all"} onValueChange={(v) => setProject(v === "all" ? null : v)}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            <SelectItem value="91game">91game</SelectItem>
            <SelectItem value="monetix">Monetix</SelectItem>
            <SelectItem value="caroussel">Caroussel</SelectItem>
          </SelectContent>
        </Select>

        {/* Status filter */}
        <Select value={status || "all"} onValueChange={(v) => setStatus(v === "all" ? null : v)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="success">Success</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
          </SelectContent>
        </Select>

        {/* Period selector */}
        <PeriodSelector />

        {/* Clear filters */}
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="gap-1">
            <X className="h-4 w-4" />
            Clear
          </Button>
        )}

        {/* Export buttons */}
        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport?.("csv")}
            disabled={isExporting}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport?.("xlsx")}
            disabled={isExporting}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Excel
          </Button>
        </div>
      </div>
    </div>
  );
}
