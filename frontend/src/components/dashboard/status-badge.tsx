import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CheckCircle, XCircle, Clock } from "lucide-react";

interface StatusBadgeProps {
  status: "success" | "failed" | "pending" | string;
  showIcon?: boolean;
  className?: string;
}

export function StatusBadge({ status, showIcon = true, className }: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase();
  
  const config = {
    success: {
      variant: "success" as const,
      label: "Success",
      icon: CheckCircle,
    },
    failed: {
      variant: "failed" as const,
      label: "Failed",
      icon: XCircle,
    },
    fail: {
      variant: "failed" as const,
      label: "Failed",
      icon: XCircle,
    },
    pending: {
      variant: "pending" as const,
      label: "Pending",
      icon: Clock,
    },
    in_progress: {
      variant: "pending" as const,
      label: "In Progress",
      icon: Clock,
    },
  };

  const statusConfig = config[normalizedStatus as keyof typeof config] || {
    variant: "default" as const,
    label: status,
    icon: null,
  };

  const Icon = statusConfig.icon;

  return (
    <Badge variant={statusConfig.variant} className={cn("gap-1", className)}>
      {showIcon && Icon && <Icon className="h-3 w-3" />}
      {statusConfig.label}
    </Badge>
  );
}
