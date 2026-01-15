import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface SourceBadgeProps {
  source: "vima" | "payshack" | string;
  className?: string;
}

export function SourceBadge({ source, className }: SourceBadgeProps) {
  const normalizedSource = source.toLowerCase();
  
  const config = {
    vima: {
      variant: "vima" as const,
      label: "Vima",
    },
    payshack: {
      variant: "payshack" as const,
      label: "PayShack",
    },
  };

  const sourceConfig = config[normalizedSource as keyof typeof config] || {
    variant: "default" as const,
    label: source,
  };

  return (
    <Badge variant={sourceConfig.variant} className={className}>
      {sourceConfig.label}
    </Badge>
  );
}
