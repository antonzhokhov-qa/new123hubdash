"use client";

import { useSyncStatus, useTriggerSync } from "@/hooks/use-sync";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatNumber, truncateId } from "@/lib/utils";
import { format, formatDistanceToNow } from "date-fns";
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Database,
  ArrowRight,
  Zap,
} from "lucide-react";
import { Source } from "@/lib/api";

export default function SyncStatusPage() {
  const { data: syncData, isLoading, refetch } = useSyncStatus();
  const triggerSync = useTriggerSync();

  const sources = syncData?.data?.sources || [];

  const handleTriggerSync = (source?: Source) => {
    triggerSync.mutate(source);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "idle":
        return <CheckCircle className="h-5 w-5 text-status-success" />;
      case "running":
        return <RefreshCw className="h-5 w-5 text-status-pending animate-spin" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-status-failed" />;
      default:
        return <Clock className="h-5 w-5 text-text-muted" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "idle":
        return "bg-status-success";
      case "running":
        return "bg-status-pending animate-pulse";
      case "failed":
        return "bg-status-failed";
      default:
        return "bg-text-muted";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Sync Status</h1>
          <p className="text-sm text-text-muted">
            Monitor and manage data synchronization from sources
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button
            onClick={() => handleTriggerSync()}
            disabled={triggerSync.isPending}
            className="gap-2"
          >
            <Zap className="h-4 w-4" />
            Sync All Sources
          </Button>
        </div>
      </div>

      {/* Source Cards */}
      <div className="grid gap-6 md:grid-cols-2">
        {isLoading ? (
          <>
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
          </>
        ) : (
          sources.map((source) => (
            <Card key={source.source} className="relative overflow-hidden">
              {/* Status indicator line */}
              <div
                className={cn(
                  "absolute top-0 left-0 right-0 h-1",
                  getStatusColor(source.status)
                )}
              />

              <CardHeader className="flex flex-row items-start justify-between pt-6">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      source.source === "vima"
                        ? "bg-blue-500/10"
                        : "bg-purple-500/10"
                    )}
                  >
                    <Database
                      className={cn(
                        "h-6 w-6",
                        source.source === "vima" ? "text-blue-400" : "text-purple-400"
                      )}
                    />
                  </div>
                  <div>
                    <CardTitle className="text-lg">
                      {source.source === "vima" ? "Vima" : "PayShack"}
                    </CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <div
                        className={cn("h-2 w-2 rounded-full", getStatusColor(source.status))}
                      />
                      <span className="text-sm text-text-secondary capitalize">
                        {source.status}
                      </span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleTriggerSync(source.source)}
                  disabled={triggerSync.isPending || source.status === "running"}
                  className="gap-1"
                >
                  <RefreshCw
                    className={cn(
                      "h-3 w-3",
                      source.status === "running" && "animate-spin"
                    )}
                  />
                  Sync
                </Button>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-text-muted">Records Synced</p>
                    <p className="text-lg font-semibold text-text-primary">
                      {formatNumber(source.records_synced)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-text-muted">Last Sync</p>
                    <p className="text-sm text-text-primary">
                      {source.last_sync_at
                        ? formatDistanceToNow(new Date(source.last_sync_at), {
                            addSuffix: true,
                          })
                        : "Never"}
                    </p>
                  </div>
                </div>

                {/* Timeline */}
                <div className="space-y-3 pt-3 border-t border-border-primary">
                  {source.last_successful_sync && (
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-4 w-4 text-status-success shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm text-text-secondary">Last successful sync</p>
                        <p className="text-xs text-text-muted">
                          {format(new Date(source.last_successful_sync), "MMM dd, yyyy HH:mm:ss")}
                        </p>
                      </div>
                    </div>
                  )}

                  {source.next_sync_at && (
                    <div className="flex items-center gap-3">
                      <Clock className="h-4 w-4 text-status-pending shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm text-text-secondary">Next scheduled sync</p>
                        <p className="text-xs text-text-muted">
                          {format(new Date(source.next_sync_at), "MMM dd, yyyy HH:mm:ss")}
                        </p>
                      </div>
                    </div>
                  )}

                  {source.last_cursor && (
                    <div className="flex items-center gap-3">
                      <ArrowRight className="h-4 w-4 text-text-muted shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm text-text-secondary">Last cursor</p>
                        <p className="text-xs font-mono text-text-muted">
                          {truncateId(source.last_cursor, 20)}
                        </p>
                      </div>
                    </div>
                  )}

                  {source.error_message && (
                    <div className="flex items-start gap-3 p-3 rounded-lg bg-status-failed-bg">
                      <XCircle className="h-4 w-4 text-status-failed shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-status-failed">Error</p>
                        <p className="text-xs text-text-secondary mt-1">
                          {source.error_message}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Info section */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-glow">
              <Zap className="h-5 w-5 text-accent-primary" />
            </div>
            <div>
              <h3 className="font-medium text-text-primary">Automatic Synchronization</h3>
              <p className="text-sm text-text-muted mt-1">
                Data is automatically synchronized every 5 minutes. Vima uses incremental sync
                with operation_create_id cursor. PayShack requires browser automation for data
                extraction.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
