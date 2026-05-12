"use client";

import { useEffect, useState } from "react";

import { PriceCard } from "@/components/shared/price-card";
import { PriceChart } from "@/components/shared/price-chart";
import { useLocale } from "@/hooks/use-locale";
import type { MarketQuote, PricePoint } from "@/lib/market-data";
import { fetchLatestQuotes, fetchPriceHistory } from "@/lib/market-data";

interface MarketDataSectionProps {
  onQuotesLoaded?: (quotes: MarketQuote[]) => void;
}

export function MarketDataSection({ onQuotesLoaded }: MarketDataSectionProps) {
  const { t } = useLocale();
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("BTC");
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([fetchLatestQuotes(), fetchPriceHistory("BTC")])
      .then(([quotesData, historyData]) => {
        if (cancelled) return;
        setQuotes(quotesData);
        setHistory(historyData.history);
        setLoading(false);
        onQuotesLoaded?.(quotesData);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load market data");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [onQuotesLoaded]);

  function handleSelectSymbol(symbol: string) {
    setSelectedSymbol(symbol);
    fetchPriceHistory(symbol)
      .then((data) => setHistory(data.history))
      .catch(() => setHistory([]));
  }

  if (loading) {
    return (
      <div className="mt-6 space-y-4 sm:mt-8 sm:space-y-6">
        <div className="h-6 w-32 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-6 shadow-sm">
              <div className="h-4 w-16 animate-pulse rounded bg-muted" />
              <div className="mt-3 h-7 w-28 animate-pulse rounded bg-muted" />
              <div className="mt-2 h-4 w-20 animate-pulse rounded bg-muted" />
            </div>
          ))}
        </div>
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="h-5 w-48 animate-pulse rounded bg-muted" />
          <div className="mt-4 h-48 animate-pulse rounded bg-muted" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-8 rounded-xl border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold">{t("dashboard.marketData")}</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {t("dashboard.marketDataError")}
        </p>
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-4 sm:mt-8 sm:space-y-6">
      <h2 className="text-lg font-semibold">{t("dashboard.marketData")}</h2>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {quotes.map((q) => (
          <PriceCard
            key={q.symbol}
            symbol={q.symbol}
            name={q.name}
            price={q.price}
            change={q.change}
            changePercent={q.change_percent}
            selected={q.symbol === selectedSymbol}
            onClick={() => handleSelectSymbol(q.symbol)}
          />
        ))}
      </div>

      {history.length > 0 && (
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="mb-4 text-base font-semibold">
            {t("dashboard.priceHistory", { symbol: selectedSymbol })}
          </h3>
          <PriceChart data={history} symbol={selectedSymbol} />
        </div>
      )}
    </div>
  );
}
