"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";
import { formatNumber } from "@/lib/utils";

interface TrendChartProps {
  title: string;
  data: Array<{
    timestamp: string;
    count: number;
    amount: number;
    success_count: number;
    failed_count: number;
  }>;
  dataKey?: "count" | "amount";
  isLoading?: boolean;
}

export function TrendChart({
  title,
  data,
  dataKey = "count",
  isLoading,
}: TrendChartProps) {
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

  const chartData = data.map((item) => ({
    ...item,
    time: format(new Date(item.timestamp), "HH:mm"),
    date: format(new Date(item.timestamp), "MMM dd"),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
            <XAxis
              dataKey="time"
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
              labelStyle={{ color: "#FAFAFA" }}
              itemStyle={{ color: "#A1A1AA" }}
              formatter={(value: number) => [formatNumber(value), ""]}
            />
            <Area
              type="monotone"
              dataKey="success_count"
              stackId="1"
              stroke="#22C55E"
              fill="url(#colorSuccess)"
              name="Success"
            />
            <Area
              type="monotone"
              dataKey="failed_count"
              stackId="1"
              stroke="#EF4444"
              fill="url(#colorFailed)"
              name="Failed"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
