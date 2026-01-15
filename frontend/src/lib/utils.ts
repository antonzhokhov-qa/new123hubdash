import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  value: number,
  currency: string = "USD",
  locale: string = "en-US"
): string {
  if (value === null || value === undefined) return "-";
  
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `${currency} ${value.toFixed(2)}`;
  }
}

export function formatNumber(
  value: number,
  options?: {
    decimals?: number;
    compact?: boolean;
  }
): string {
  if (value === null || value === undefined) return "-";
  
  const { decimals = 0, compact = false } = options || {};
  
  if (compact && Math.abs(value) >= 1000) {
    const suffixes = ["", "K", "M", "B", "T"];
    const tier = Math.floor(Math.log10(Math.abs(value)) / 3);
    const suffix = suffixes[Math.min(tier, suffixes.length - 1)];
    const scaled = value / Math.pow(1000, tier);
    return `${scaled.toFixed(1)}${suffix}`;
  }
  
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function truncateId(id: string | undefined | null, length: number = 8): string {
  if (!id) return "-";
  if (id.length <= length) return id;
  return `${id.slice(0, length)}...`;
}

export function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  
  // Fallback for older browsers
  return new Promise((resolve, reject) => {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
      document.execCommand("copy");
      resolve();
    } catch (err) {
      reject(err);
    } finally {
      document.body.removeChild(textarea);
    }
  });
}

export function formatDate(
  date: string | Date,
  options?: Intl.DateTimeFormatOptions
): string {
  if (!date) return "-";
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  };
  
  return new Intl.DateTimeFormat("en-US", defaultOptions).format(
    typeof date === "string" ? new Date(date) : date
  );
}

export function formatPercent(value: number, decimals: number = 1): string {
  if (value === null || value === undefined) return "-";
  return `${value.toFixed(decimals)}%`;
}
