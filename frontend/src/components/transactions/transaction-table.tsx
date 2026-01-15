"use client";

import { useState } from "react";
import { Transaction } from "@/lib/api";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { SourceBadge } from "@/components/dashboard/source-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, truncateId, copyToClipboard, cn } from "@/lib/utils";
import { format } from "date-fns";
import {
  ChevronLeft,
  ChevronRight,
  Copy,
  ExternalLink,
  ArrowUpDown,
} from "lucide-react";

interface TransactionTableProps {
  data: Transaction[];
  meta?: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
  isLoading?: boolean;
  onPageChange?: (page: number) => void;
  onRowClick?: (transaction: Transaction) => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (column: string) => void;
}

export function TransactionTable({
  data,
  meta,
  isLoading,
  onPageChange,
  onRowClick,
  sortBy,
  sortOrder,
  onSort,
}: TransactionTableProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (text: string, id: string) => {
    await copyToClipboard(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const SortableHeader = ({
    column,
    children,
  }: {
    column: string;
    children: React.ReactNode;
  }) => (
    <TableHead
      className="cursor-pointer hover:text-text-primary transition-colors"
      onClick={() => onSort?.(column)}
    >
      <div className="flex items-center gap-1">
        {children}
        <ArrowUpDown
          className={cn(
            "h-3 w-3",
            sortBy === column ? "text-accent-primary" : "text-text-muted"
          )}
        />
      </div>
    </TableHead>
  );

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-4 px-4 py-3 bg-background-tertiary rounded-lg">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-20" />
          ))}
        </div>
        {Array.from({ length: 10 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="rounded-full bg-background-tertiary p-4 mb-4">
          <ExternalLink className="h-8 w-8 text-text-muted" />
        </div>
        <p className="text-lg font-medium text-text-primary">No transactions found</p>
        <p className="text-sm text-text-muted mt-1">
          Try adjusting your filters or date range
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border-primary overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Source</TableHead>
              <TableHead>ID / c_id</TableHead>
              <TableHead>Project</TableHead>
              <SortableHeader column="amount">Amount</SortableHeader>
              <TableHead>Status</TableHead>
              <TableHead>User</TableHead>
              <SortableHeader column="created_at">Created</SortableHeader>
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((txn) => (
              <TableRow
                key={txn.id}
                className="cursor-pointer"
                onClick={() => onRowClick?.(txn)}
              >
                <TableCell>
                  <SourceBadge source={txn.source} />
                </TableCell>
                <TableCell>
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-1">
                      <span className="font-mono text-xs">
                        {truncateId(txn.source_id, 12)}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopy(txn.source_id, `src-${txn.id}`);
                        }}
                        className="text-text-muted hover:text-text-primary"
                      >
                        <Copy
                          className={cn(
                            "h-3 w-3",
                            copiedId === `src-${txn.id}` && "text-status-success"
                          )}
                        />
                      </button>
                    </div>
                    {txn.client_operation_id && (
                      <div className="flex items-center gap-1">
                        <span className="font-mono text-xs text-text-muted">
                          c_id: {truncateId(txn.client_operation_id, 10)}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopy(txn.client_operation_id!, `cid-${txn.id}`);
                          }}
                          className="text-text-muted hover:text-text-primary"
                        >
                          <Copy
                            className={cn(
                              "h-3 w-3",
                              copiedId === `cid-${txn.id}` && "text-status-success"
                            )}
                          />
                        </button>
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-text-secondary">{txn.project || "-"}</span>
                </TableCell>
                <TableCell>
                  <span className="font-medium">
                    {formatCurrency(txn.amount, txn.currency)}
                  </span>
                </TableCell>
                <TableCell>
                  <StatusBadge status={txn.status} />
                </TableCell>
                <TableCell>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm truncate max-w-[150px]">
                      {txn.user_name || txn.user_email || "-"}
                    </span>
                    {txn.user_phone && (
                      <span className="text-xs text-text-muted">{txn.user_phone}</span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm">
                      {format(new Date(txn.created_at), "MMM dd, yyyy")}
                    </span>
                    <span className="text-xs text-text-muted">
                      {format(new Date(txn.created_at), "HH:mm:ss")}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {meta && meta.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted">
            Showing {(meta.page - 1) * meta.limit + 1} to{" "}
            {Math.min(meta.page * meta.limit, meta.total)} of {meta.total} results
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(meta.page - 1)}
              disabled={meta.page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, meta.total_pages) }, (_, i) => {
                const page = i + 1;
                return (
                  <Button
                    key={page}
                    variant={meta.page === page ? "default" : "ghost"}
                    size="sm"
                    className="w-8 h-8"
                    onClick={() => onPageChange?.(page)}
                  >
                    {page}
                  </Button>
                );
              })}
              {meta.total_pages > 5 && (
                <>
                  <span className="text-text-muted">...</span>
                  <Button
                    variant={meta.page === meta.total_pages ? "default" : "ghost"}
                    size="sm"
                    className="w-8 h-8"
                    onClick={() => onPageChange?.(meta.total_pages)}
                  >
                    {meta.total_pages}
                  </Button>
                </>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(meta.page + 1)}
              disabled={meta.page === meta.total_pages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
