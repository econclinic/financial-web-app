"use client";

import { useEffect, useState } from "react";
import { Eye, Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useAuth } from "@/hooks/use-auth";
import { useLocale } from "@/hooks/use-locale";
import type { MarketPriceInfo } from "@/lib/portfolio";
import { fetchMarketPrices } from "@/lib/portfolio";
import type { WatchlistItem } from "@/lib/watchlist";
import { addToWatchlist, fetchWatchlist, removeFromWatchlist } from "@/lib/watchlist";

export default function WatchlistPage() {
  const { token } = useAuth();
  const { t } = useLocale();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [prices, setPrices] = useState<Record<string, MarketPriceInfo>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function load() {
      try {
        const list = await fetchWatchlist(token!);
        if (cancelled) return;
        setItems(list);
        if (list.length > 0) {
          try {
            const p = await fetchMarketPrices(token!, list.map((i) => i.symbol));
            if (cancelled) return;
            setPrices(p);
          } catch {
            // prices unavailable — show N/A
          }
        } else {
          setPrices({});
        }
      } catch (err: unknown) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load watchlist");
      }
      if (!cancelled) setLoading(false);
    }

    load();
    return () => { cancelled = true; };
  }, [token, refreshKey]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !symbol.trim()) return;
    setAddError(null);
    setAdding(true);
    try {
      await addToWatchlist(token, symbol.trim());
      setSymbol("");
      setRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed to add symbol");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(sym: string) {
    if (!token) return;
    setRemoving(sym);
    try {
      await removeFromWatchlist(token, sym);
      setRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove symbol");
    } finally {
      setRemoving(null);
    }
  }

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8">
          <div className="flex items-center gap-2">
            <Eye className="h-6 w-6" />
            <h2 className="text-2xl font-bold tracking-tight">{t("watchlist.title")}</h2>
          </div>

          {/* Add symbol form */}
          <form onSubmit={handleAdd} className="mt-6 flex flex-wrap items-center gap-3">
            <input
              type="text"
              placeholder={t("watchlist.placeholder")}
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
            <Button type="submit" size="sm" disabled={adding || !symbol.trim()}>
              {adding ? (
                <Loader2 className="h-4 w-4 animate-spin ltr:mr-1.5 rtl:ml-1.5" />
              ) : (
                <Plus className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
              )}
              {t("watchlist.add")}
            </Button>
          </form>

          {addError && (
            <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {addError}
            </div>
          )}

          {loading && (
            <div className="mt-8 flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("watchlist.loading")}
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="mt-8 rounded-xl border bg-muted/40 p-8 text-center text-muted-foreground">
              <Eye className="mx-auto h-8 w-8 mb-2" />
              <p>{t("watchlist.empty")}</p>
              <p className="text-sm mt-1">{t("watchlist.emptyHint")}</p>
            </div>
          )}

          {!loading && items.length > 0 && (
            <div className="mt-6 -mx-4 overflow-x-auto sm:mx-0 sm:rounded-xl sm:border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40">
                    <th className="px-4 py-3 text-start font-medium">{t("watchlist.title")}</th>
                    <th className="px-4 py-3 text-end font-medium">{t("watchlist.currentPrice")}</th>
                    <th className="px-4 py-3 text-end font-medium">{t("watchlist.change24h")}</th>
                    <th className="px-4 py-3 text-end font-medium">{t("watchlist.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const priceInfo = prices[item.symbol];
                    const price = priceInfo?.price;
                    const change = priceInfo?.change_24h;
                    return (
                      <tr key={item.id} className="border-b last:border-b-0">
                        <td className="px-4 py-3 font-medium">{item.symbol}</td>
                        <td className="px-4 py-3 text-end tabular-nums">
                          {price != null
                            ? `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                            : "N/A"}
                        </td>
                        <td className={`px-4 py-3 text-end tabular-nums ${change != null && change >= 0 ? "text-green-600" : "text-red-600"}`}>
                          {change != null ? `${change >= 0 ? "+" : ""}${change.toFixed(2)}%` : "—"}
                        </td>
                        <td className="px-4 py-3 text-end">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRemove(item.symbol)}
                            disabled={removing === item.symbol}
                          >
                            {removing === item.symbol ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                            <span className="ltr:ml-1.5 rtl:mr-1.5">{t("watchlist.remove")}</span>
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
