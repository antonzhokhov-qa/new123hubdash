"use client";

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber, formatCurrency } from "@/lib/utils";

interface BarChartProps {
  title: string;
  data: Array<{
    name: string;
    value: number;
    secondaryValue?: number;
  }>;
  valueType?: "count" | "amount";
  isLoading?: boolean;
  layout?: "horizontal" | "vertical";
}

const COLORS = ["#6366F1", "#8B5CF6", "#A855F7", "#D946EF", "#EC4899"];

export function BarChart({
  title,
  data,
  valueType = "count",
  isLoading,
  layout = "horizontal",
}: BarChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const formatValue = (value: number) =>
    valueType === "amount" ? formatCurrency(value, "INR") : formatNumber(value);

  if (layout === "horizontal") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <RechartsBarChart data={data} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272A" horizontal={false} />
              <XAxis
                type="number"
                stroke="#71717A"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => formatNumber(value)}
              />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#71717A"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                width={80}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1A1A24",
                  border: "1px solid #27272A",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => [formatValue(value), ""]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </RechartsBarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <RechartsBarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
            <XAxis
              dataKey="name"
              stroke="#71717A"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#71717A"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => formatNumber(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1A1A24",
                border: "1px solid #27272A",
                borderRadius: "8px",
              }}
              formatter={(value: number) => [formatValue(value), ""]}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
