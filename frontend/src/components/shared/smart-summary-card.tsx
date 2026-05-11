"use client";

import { ArrowDown, ArrowUp, Sparkles, TrendingDown, TrendingUp } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";
import type { MarketQuote } from "@/lib/market-data";

interface SmartSummaryCardProps {
  quotes: MarketQuote[];
}

export function SmartSummaryCard({ quotes }: SmartSummaryCardProps) {
  const { t } = useLocale();

  if (quotes.length === 0) return null;

  const totalAbsChange = quotes.reduce((sum, q) => sum + q.change, 0);
  const avgPctChange =
    quotes.reduce((sum, q) => sum + q.change_percent, 0) / quotes.length;

  const sorted = [...quotes].sort(
    (a, b) => b.change_percent - a.change_percent,
  );
  const best = sorted[0];
  const worst = sorted[sorted.length - 1];

  const marketUp = avgPctChange >= 0;

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm sm:p-6">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <h2 className="text-base font-semibold">{t("summary.title")}</h2>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {/* Market trend */}
        <div className="flex items-start gap-3 rounded-lg bg-muted/50 p-3">
          {marketUp ? (
            <TrendingUp className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
          ) : (
            <TrendingDown className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          )}
          <div className="min-w-0">
            <p className="text-xs font-medium text-muted-foreground">
              {t("summary.marketTrend")}
            </p>
            <p
              className={`text-lg font-semibold ${marketUp ? "text-green-500" : "text-red-500"}`}
            >
              {marketUp ? "+" : ""}
              {avgPctChange.toFixed(2)}%
            </p>
            <p className="text-xs text-muted-foreground">
              {marketUp ? "+" : ""}
              {totalAbsChange.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}{" "}
              {t("summary.combined")}
            </p>
          </div>
        </div>

        {/* Best performer */}
        <div className="flex items-start gap-3 rounded-lg bg-muted/50 p-3">
          <ArrowUp className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
          <div className="min-w-0">
            <p className="text-xs font-medium text-muted-foreground">
              {t("summary.bestPerformer")}
            </p>
            <p className="truncate text-lg font-semibold">{best.symbol}</p>
            <p className="text-xs font-medium text-green-500">
              {best.change_percent >= 0 ? "+" : ""}
              {best.change_percent.toFixed(2)}%
              <span className="text-muted-foreground">
                {" "}({best.change >= 0 ? "+" : ""}
                {best.change.toFixed(2)})
              </span>
            </p>
          </div>
        </div>

        {/* Worst performer */}
        <div className="flex items-start gap-3 rounded-lg bg-muted/50 p-3">
          <ArrowDown className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div className="min-w-0">
            <p className="text-xs font-medium text-muted-foreground">
              {t("summary.worstPerformer")}
            </p>
            <p className="truncate text-lg font-semibold">{worst.symbol}</p>
            <p className="text-xs font-medium text-red-500">
              {worst.change_percent >= 0 ? "+" : ""}
              {worst.change_percent.toFixed(2)}%
              <span className="text-muted-foreground">
                {" "}({worst.change >= 0 ? "+" : ""}
                {worst.change.toFixed(2)})
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
