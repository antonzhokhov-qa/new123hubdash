"use client";

import { useFilterStore, DisplayCurrency } from "@/stores/filter-store";
import { cn } from "@/lib/utils";
import { DollarSign, IndianRupee } from "lucide-react";

const currencies: { id: DisplayCurrency; label: string; icon: typeof DollarSign }[] = [
  { id: "USD", label: "$", icon: DollarSign },
  { id: "INR", label: "₹", icon: IndianRupee },
];

export function CurrencyToggle() {
  const { displayCurrency, setDisplayCurrency } = useFilterStore();

  return (
    <div className="flex items-center gap-0.5 rounded-lg bg-background-secondary p-1 border border-border-primary">
      {currencies.map((currency) => {
        const isActive = displayCurrency === currency.id;
        const Icon = currency.icon;
        return (
          <button
            key={currency.id}
            onClick={() => setDisplayCurrency(currency.id)}
            className={cn(
              "flex items-center justify-center w-8 h-7 rounded-md text-sm font-medium transition-all",
              isActive
                ? "bg-accent-primary text-white shadow-sm"
                : "text-text-secondary hover:text-text-primary hover:bg-background-tertiary"
            )}
            title={`Display in ${currency.id}`}
          >
            <Icon className="h-4 w-4" />
          </button>
        );
      })}
    </div>
  );
}
