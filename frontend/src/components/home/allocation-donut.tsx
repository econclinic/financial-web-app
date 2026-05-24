"use client";

import Link from "next/link";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { PieChartIcon } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";
import type { AllocationData } from "@/hooks/use-portfolio-allocation";

interface AllocationDonutProps {
  data: AllocationData | null;
  loading: boolean;
  error: string | null;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

export function AllocationDonut({ data, loading, error }: AllocationDonutProps) {
  const { t } = useLocale();

  if (loading) {
    return (
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="h-4 w-28 animate-pulse rounded bg-muted" />
        <div className="mx-auto mt-4 h-40 w-40 animate-pulse rounded-full bg-muted" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <p className="text-sm text-muted-foreground">{t("home.allocationUnavailable" as never)}</p>
      </div>
    );
  }

  const hasAssets = data.assets.length > 0;

  const chartData = data.assets.map((a) => ({
    name: a.symbol,
    value: a.value,
    weight: a.weight,
  }));

  return (
    <Link href="/portfolio" className="block">
      <div className="rounded-xl border bg-card p-6 shadow-sm transition-shadow hover:shadow-md">
        <div className="flex items-center gap-2">
          <PieChartIcon className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium text-muted-foreground">
            {t("home.allocation" as never)}
          </span>
        </div>

        {hasAssets ? (
          <div className="mt-4">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  dataKey="value"
                  stroke="none"
                >
                  {chartData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) =>
                    `$${Number(value).toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                  }
                />
              </PieChart>
            </ResponsiveContainer>

            <div className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1">
              {chartData.slice(0, 5).map((item, index) => (
                <div key={item.name} className="flex items-center gap-1.5 text-xs">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-muted-foreground">
                    {item.name}
                    {item.weight != null ? ` ${(item.weight * 100).toFixed(0)}%` : ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="mt-6 text-center text-sm text-muted-foreground">
            {t("home.noPositions" as never)}
          </p>
        )}
      </div>
    </Link>
  );
}
