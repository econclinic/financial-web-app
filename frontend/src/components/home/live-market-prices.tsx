"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";
import type { MarketQuote } from "@/lib/market-data";
import { fetchLatestQuotes } from "@/lib/market-data";

function formatPrice(price: number): string {
  return price.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function LiveMarketPrices() {
  const { t } = useLocale();
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchLatestQuotes()
      .then((data) => {
        if (!cancelled) {
          setQuotes(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load prices");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <section id="market-prices" className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="h-5 w-32 animate-pulse rounded bg-muted" />
        <div className="mt-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="h-4 w-20 animate-pulse rounded bg-muted" />
              <div className="h-4 w-24 animate-pulse rounded bg-muted" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section id="market-prices" className="rounded-xl border bg-card p-6 shadow-sm">
        <h3 className="text-base font-semibold">{t("home.liveMarket" as never)}</h3>
        <p className="mt-2 text-sm text-muted-foreground">{t("dashboard.marketDataError")}</p>
      </section>
    );
  }

  return (
    <section id="market-prices" className="rounded-xl border bg-card p-6 shadow-sm">
      <h3 className="text-base font-semibold">{t("home.liveMarket" as never)}</h3>

      <div className="mt-4 divide-y">
        {quotes.map((q) => {
          const isPositive = q.change >= 0;
          return (
            <div key={q.symbol} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
              <div>
                <p className="font-medium">{q.symbol}</p>
                <p className="text-xs text-muted-foreground">{q.name}</p>
              </div>
              <div className="text-right ltr:text-right rtl:text-left">
                <p className="font-medium">{formatPrice(q.price)}</p>
                <div className="flex items-center justify-end gap-1">
                  {isPositive ? (
                    <ArrowUpRight className="h-3 w-3 text-green-500" />
                  ) : (
                    <ArrowDownRight className="h-3 w-3 text-red-500" />
                  )}
                  <span className={`text-xs font-medium ${isPositive ? "text-green-500" : "text-red-500"}`}>
                    {isPositive ? "+" : ""}{q.change_percent.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
