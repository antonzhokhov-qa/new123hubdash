"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber, formatCurrency } from "@/lib/utils";

interface DonutChartProps {
  title: string;
  data: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  valueType?: "count" | "amount";
  isLoading?: boolean;
}

const COLORS = {
  success: "#22C55E",
  failed: "#EF4444",
  pending: "#F59E0B",
  vima: "#3B82F6",
  payshack: "#A855F7",
};

export function DonutChart({
  title,
  data,
  valueType = "count",
  isLoading,
}: DonutChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center">
          <Skeleton className="h-[200px] w-[200px] rounded-full" />
        </CardContent>
      </Card>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    if (percent < 0.05) return null;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * (Math.PI / 180));
    const y = cy + radius * Math.sin(-midAngle * (Math.PI / 180));

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={12}
        fontWeight={500}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
              labelLine={false}
              label={renderCustomLabel}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "#1A1A24",
                border: "1px solid #27272A",
                borderRadius: "8px",
              }}
              formatter={(value: number) => [
                valueType === "amount"
                  ? formatCurrency(value, "INR")
                  : formatNumber(value),
                "",
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => (
                <span className="text-sm text-text-secondary">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center -mt-8">
            <p className="text-2xl font-bold text-text-primary">
              {valueType === "amount" ? formatCurrency(total, "INR") : formatNumber(total)}
            </p>
            <p className="text-xs text-text-muted">Total</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
