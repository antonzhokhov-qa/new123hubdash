"use client";

import { Bell, RefreshCw, Settings, User, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSyncStatus } from "@/hooks/use-sync";
import { useWebSocketStatus } from "@/hooks/use-websocket";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

export function Header() {
  const { data: syncStatus, isLoading, refetch } = useSyncStatus();
  const { status: wsStatus, isConnected: wsConnected, statusText: wsText } = useWebSocketStatus();

  const lastSync = syncStatus?.data?.sources?.[0]?.last_sync_at;
  const isAllHealthy = syncStatus?.data?.sources?.every(
    (s) => s.status !== "failed"
  );

  return (
    <header className="flex h-16 items-center justify-between border-b border-border-primary bg-background-secondary px-6">
      {/* Left side - Status indicators */}
      <div className="flex items-center gap-4">
        {/* Sync status */}
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              isLoading
                ? "bg-text-muted animate-pulse"
                : isAllHealthy
                ? "bg-status-success"
                : "bg-status-failed"
            )}
          />
          <span className="text-sm text-text-secondary">
            {isLoading
              ? "Checking..."
              : isAllHealthy
              ? "All systems operational"
              : "Sync issues detected"}
          </span>
        </div>
        {lastSync && (
          <span className="text-xs text-text-muted">
            Last sync: {format(new Date(lastSync), "HH:mm:ss")}
          </span>
        )}
        
        {/* WebSocket status */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-background-tertiary">
          {wsConnected ? (
            <Wifi className="h-3.5 w-3.5 text-status-success" />
          ) : (
            <WifiOff className="h-3.5 w-3.5 text-text-muted" />
          )}
          <span className={cn(
            "text-xs",
            wsConnected ? "text-status-success" : "text-text-muted"
          )}>
            {wsText}
          </span>
        </div>
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => refetch()}
          className="text-text-secondary hover:text-text-primary"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-text-secondary hover:text-text-primary relative"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-status-failed" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-text-secondary hover:text-text-primary"
        >
          <Settings className="h-4 w-4" />
        </Button>
        <div className="ml-2 h-8 w-px bg-border-primary" />
        <Button
          variant="ghost"
          className="gap-2 text-text-secondary hover:text-text-primary"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-background-tertiary">
            <User className="h-4 w-4" />
          </div>
          <span className="text-sm">Admin</span>
        </Button>
      </div>
    </header>
  );
}
