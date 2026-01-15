import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default:
          "bg-background-tertiary text-text-secondary",
        success:
          "bg-status-success-bg text-status-success",
        failed:
          "bg-status-failed-bg text-status-failed",
        pending:
          "bg-status-pending-bg text-status-pending",
        vima:
          "bg-blue-500/10 text-blue-400",
        payshack:
          "bg-purple-500/10 text-purple-400",
        outline:
          "border border-border-primary text-text-secondary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
