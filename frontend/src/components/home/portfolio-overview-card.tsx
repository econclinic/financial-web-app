"use client";

import Link from "next/link";
import { ArrowUpRight, ArrowDownRight, TrendingUp } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";
import type { PerformanceSummary } from "@/hooks/use-portfolio-performance";

interface PortfolioOverviewCardProps {
  data: PerformanceSummary | null;
  loading: boolean;
  error: string | null;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function PortfolioOverviewCard({ data, loading, error }: PortfolioOverviewCardProps) {
  const { t } = useLocale();

  if (loading) {
    return (
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="mt-4 h-8 w-40 animate-pulse rounded bg-muted" />
        <div className="mt-3 h-4 w-32 animate-pulse rounded bg-muted" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <p className="text-sm text-muted-foreground">{t("home.portfolioUnavailable" as never)}</p>
      </div>
    );
  }

  const value = data?.ending_value ?? 0;
  const change = data?.absolute_return ?? 0;
  const changePct = data?.total_return_pct ?? 0;
  const isPositive = change >= 0;

  return (
    <Link href="/dashboard/analytics" className="block">
      <div className="rounded-xl border bg-card p-6 shadow-sm transition-shadow hover:shadow-md">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium text-muted-foreground">
            {t("home.portfolioOverview" as never)}
          </span>
        </div>

        <p className="mt-3 text-2xl font-bold sm:text-3xl">{formatCurrency(value)}</p>

        <div className="mt-2 flex items-center gap-1.5">
          {isPositive ? (
            <ArrowUpRight className="h-4 w-4 text-green-500" />
          ) : (
            <ArrowDownRight className="h-4 w-4 text-red-500" />
          )}
          <span className={`text-sm font-medium ${isPositive ? "text-green-500" : "text-red-500"}`}>
            {formatCurrency(Math.abs(change))} ({formatPercent(changePct)})
          </span>
          <span className="text-xs text-muted-foreground">7d</span>
        </div>
      </div>
    </Link>
  );
}
