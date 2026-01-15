"use client";

import { Transaction } from "@/lib/api";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { SourceBadge } from "@/components/dashboard/source-badge";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";
import { format } from "date-fns";
import {
  X,
  Copy,
  ExternalLink,
  User,
  Mail,
  Phone,
  Globe,
  Calendar,
  Hash,
  CreditCard,
  CheckCircle,
} from "lucide-react";
import { useState } from "react";

interface TransactionDetailModalProps {
  transaction: Transaction;
  onClose: () => void;
}

function InfoRow({
  icon: Icon,
  label,
  value,
  copyable = false,
}: {
  icon?: any;
  label: string;
  value: string | number | null | undefined;
  copyable?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (value) {
      navigator.clipboard.writeText(String(value));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-border-primary last:border-0">
      <div className="flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4 text-text-muted" />}
        <span className="text-sm text-text-secondary">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={cn("text-sm font-medium text-text-primary", !value && "text-text-muted")}>
          {value || "-"}
        </span>
        {copyable && value && (
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-background-tertiary transition-colors"
            title="Copy"
          >
            {copied ? (
              <CheckCircle className="h-3.5 w-3.5 text-status-success" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-text-muted" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export function TransactionDetailModal({
  transaction: txn,
  onClose,
}: TransactionDetailModalProps) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-background-primary rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-primary bg-background-secondary">
          <div className="flex items-center gap-3">
            <SourceBadge source={txn.source} />
            <div>
              <h2 className="font-semibold text-text-primary">Transaction Details</h2>
              <p className="text-xs text-text-muted font-mono">
                {txn.client_operation_id || txn.source_id}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={txn.status} size="lg" />
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-130px)]">
          {/* Amount Section */}
          <div className="mb-6 p-4 rounded-xl bg-background-secondary text-center">
            <p className="text-sm text-text-muted mb-1">Amount</p>
            <p className="text-3xl font-bold text-text-primary">
              {formatCurrency(txn.amount, txn.currency)}
            </p>
            {txn.fee && (
              <p className="text-sm text-text-muted mt-1">
                Fee: {formatCurrency(txn.fee, txn.currency)}
              </p>
            )}
          </div>

          {/* IDs Section */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-text-primary mb-3 flex items-center gap-2">
              <Hash className="h-4 w-4" /> Identifiers
            </h3>
            <div className="rounded-lg bg-background-secondary p-3">
              <InfoRow icon={Hash} label="ID" value={txn.id} copyable />
              <InfoRow icon={Hash} label="Source ID" value={txn.source_id} copyable />
              <InfoRow icon={Hash} label="Reference ID" value={txn.reference_id} copyable />
              <InfoRow icon={Hash} label="Client Operation ID" value={txn.client_operation_id} copyable />
              <InfoRow icon={Hash} label="Order ID" value={txn.order_id} copyable />
              {txn.utr && <InfoRow icon={Hash} label="UTR" value={txn.utr} copyable />}
            </div>
          </div>

          {/* User Section */}
          {(txn.user_email || txn.user_phone || txn.user_name) && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-text-primary mb-3 flex items-center gap-2">
                <User className="h-4 w-4" /> Customer
              </h3>
              <div className="rounded-lg bg-background-secondary p-3">
                {txn.user_name && <InfoRow icon={User} label="Name" value={txn.user_name} />}
                <InfoRow icon={Hash} label="User ID" value={txn.user_id} copyable />
                <InfoRow icon={Mail} label="Email" value={txn.user_email} copyable />
                <InfoRow icon={Phone} label="Phone" value={txn.user_phone} copyable />
              </div>
            </div>
          )}

          {/* Transaction Details */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-text-primary mb-3 flex items-center gap-2">
              <CreditCard className="h-4 w-4" /> Details
            </h3>
            <div className="rounded-lg bg-background-secondary p-3">
              <InfoRow icon={Globe} label="Country" value={txn.country} />
              <InfoRow label="Project" value={txn.project} />
              <InfoRow label="Merchant ID" value={txn.merchant_id} />
              <InfoRow label="Payment Method" value={txn.payment_method} />
              <InfoRow label="Payment Product" value={txn.payment_product} />
              <InfoRow label="Original Status" value={txn.original_status} />
            </div>
          </div>

          {/* Timestamps */}
          <div>
            <h3 className="text-sm font-medium text-text-primary mb-3 flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Timeline
            </h3>
            <div className="rounded-lg bg-background-secondary p-3">
              <InfoRow
                icon={Calendar}
                label="Created"
                value={format(new Date(txn.created_at), "PPpp")}
              />
              {txn.updated_at && (
                <InfoRow
                  icon={Calendar}
                  label="Updated"
                  value={format(new Date(txn.updated_at), "PPpp")}
                />
              )}
              {txn.completed_at && (
                <InfoRow
                  icon={Calendar}
                  label="Completed"
                  value={format(new Date(txn.completed_at), "PPpp")}
                />
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-border-primary bg-background-secondary">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
