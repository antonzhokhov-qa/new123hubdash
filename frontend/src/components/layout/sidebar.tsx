"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import {
  LayoutDashboard,
  ArrowLeftRight,
  RefreshCw,
  Activity,
  Store,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Transactions",
    href: "/transactions",
    icon: ArrowLeftRight,
  },
  {
    name: "Merchants",
    href: "/merchants",
    icon: Store,
  },
  {
    name: "Reconciliation",
    href: "/reconciliation",
    icon: RefreshCw,
  },
  {
    name: "Sync Status",
    href: "/sync",
    icon: Activity,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <div
      className={cn(
        "relative flex flex-col bg-background-secondary border-r border-border-primary transition-all duration-300",
        sidebarCollapsed ? "w-[72px]" : "w-[240px]"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 px-4 border-b border-border-primary">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-primary">
          <span className="text-lg font-bold text-white">P</span>
        </div>
        {!sidebarCollapsed && (
          <span className="font-semibold text-text-primary">PSP Dashboard</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-accent-glow text-accent-primary"
                  : "text-text-secondary hover:bg-background-tertiary hover:text-text-primary"
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5 shrink-0",
                  isActive ? "text-accent-primary" : "text-text-muted"
                )}
              />
              {!sidebarCollapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border-primary bg-background-secondary text-text-muted hover:text-text-primary hover:bg-background-tertiary transition-colors"
      >
        {sidebarCollapsed ? (
          <ChevronRight className="h-3.5 w-3.5" />
        ) : (
          <ChevronLeft className="h-3.5 w-3.5" />
        )}
      </button>

      {/* Footer */}
      <div className="border-t border-border-primary p-3">
        <div
          className={cn(
            "flex items-center gap-2 text-xs text-text-muted",
            sidebarCollapsed && "justify-center"
          )}
        >
          {!sidebarCollapsed && <span>v0.1.0</span>}
        </div>
      </div>
    </div>
  );
}
