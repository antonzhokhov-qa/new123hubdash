import { create } from "zustand";
import { startOfDay, endOfDay, subDays, format } from "date-fns";

export type DateRangePreset = "today" | "yesterday" | "last7days" | "last30days" | "custom";

interface DateRange {
  from: Date;
  to: Date;
}

export type DisplayCurrency = "USD" | "INR";

interface FilterStore {
  // Period
  dateRangePreset: DateRangePreset;
  dateRange: DateRange;
  setDateRangePreset: (preset: DateRangePreset) => void;
  setDateRange: (range: DateRange) => void;
  
  // Filters
  source: string | null;
  project: string | null;
  status: string | null;
  search: string;
  
  // Currency display
  displayCurrency: DisplayCurrency;
  setDisplayCurrency: (currency: DisplayCurrency) => void;
  
  setSource: (source: string | null) => void;
  setProject: (project: string | null) => void;
  setStatus: (status: string | null) => void;
  setSearch: (search: string) => void;
  resetFilters: () => void;
  
  // Helpers
  getDateParams: () => { from_date: string; to_date: string };
}

const today = new Date();

const getDateRangeFromPreset = (preset: DateRangePreset): DateRange => {
  const today = new Date();
  switch (preset) {
    case "today":
      return { from: startOfDay(today), to: endOfDay(today) };
    case "yesterday":
      const yesterday = subDays(today, 1);
      return { from: startOfDay(yesterday), to: endOfDay(yesterday) };
    case "last7days":
      return { from: startOfDay(subDays(today, 6)), to: endOfDay(today) };
    case "last30days":
      return { from: startOfDay(subDays(today, 29)), to: endOfDay(today) };
    default:
      return { from: startOfDay(today), to: endOfDay(today) };
  }
};

export const useFilterStore = create<FilterStore>((set, get) => ({
  dateRangePreset: "today",
  dateRange: getDateRangeFromPreset("today"),
  
  source: null,
  project: null,
  status: null,
  search: "",
  
  displayCurrency: "USD",
  
  setDateRangePreset: (preset) => {
    const dateRange = getDateRangeFromPreset(preset);
    set({ dateRangePreset: preset, dateRange });
  },
  
  setDateRange: (range) => {
    set({ dateRange: range, dateRangePreset: "custom" });
  },
  
  setSource: (source) => set({ source }),
  setProject: (project) => set({ project }),
  setStatus: (status) => set({ status }),
  setSearch: (search) => set({ search }),
  setDisplayCurrency: (currency) => set({ displayCurrency: currency }),
  
  resetFilters: () => set({
    source: null,
    project: null,
    status: null,
    search: "",
  }),
  
  getDateParams: () => {
    const { dateRange } = get();
    return {
      from_date: format(dateRange.from, "yyyy-MM-dd"),
      to_date: format(dateRange.to, "yyyy-MM-dd"),
    };
  },
}));
