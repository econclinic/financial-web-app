"use client";

import { useEffect, useState } from "react";
import { Bell, Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useAuth } from "@/hooks/use-auth";
import type { Alert } from "@/lib/alerts";
import { createAlert, deleteAlert, fetchAlerts } from "@/lib/alerts";

const SUPPORTED_SYMBOLS = ["BTC", "ETH", "AAPL"];

export default function AlertsPage() {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [symbol, setSymbol] = useState("BTC");
  const [direction, setDirection] = useState("above");
  const [targetPrice, setTargetPrice] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function load() {
      try {
        const list = await fetchAlerts(token!);
        if (cancelled) return;
        setAlerts(list);
      } catch (err: unknown) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load alerts");
      }
      if (!cancelled) setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [token, refreshKey]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !targetPrice) return;
    setAddError(null);
    setAdding(true);
    try {
      await createAlert(token, symbol, parseFloat(targetPrice), direction);
      setTargetPrice("");
      setRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed to create alert");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(alertId: number) {
    if (!token) return;
    setDeleting(alertId);
    try {
      await deleteAlert(token, alertId);
      setRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete alert");
    } finally {
      setDeleting(null);
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString();
  }

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8">
          <div className="flex items-center gap-2">
            <Bell className="h-6 w-6" />
            <h2 className="text-2xl font-bold tracking-tight">Price Alerts</h2>
          </div>

          {/* Create alert form */}
          <form onSubmit={handleCreate} className="mt-6 grid grid-cols-2 items-end gap-3 sm:flex sm:flex-wrap">
            <div>
              <label className="mb-1 block text-sm font-medium">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {SUPPORTED_SYMBOLS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Direction</label>
              <select
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="above">Above</option>
                <option value="below">Below</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Target Price ($)</label>
              <input
                type="number"
                step="any"
                min="0.01"
                placeholder="e.g. 100000"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                className="h-9 w-36 rounded-md border border-input bg-background px-3 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <Button type="submit" size="sm" disabled={adding || !targetPrice}>
              {adding ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-1.5 h-4 w-4" />
              )}
              Create Alert
            </Button>
          </form>

          {addError && (
            <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {addError}
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="mt-8 flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading alerts...
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && alerts.length === 0 && (
            <div className="mt-8 rounded-xl border bg-muted/40 p-8 text-center text-muted-foreground">
              <Bell className="mx-auto h-8 w-8 mb-2" />
              <p>No alerts set.</p>
              <p className="text-sm mt-1">Create an alert above to get started.</p>
            </div>
          )}

          {/* Alerts table */}
          {!loading && alerts.length > 0 && (
            <div className="mt-6 -mx-4 overflow-x-auto sm:mx-0 sm:rounded-xl sm:border">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/40">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Symbol</th>
                    <th className="px-4 py-3 text-left font-medium">Condition</th>
                    <th className="px-4 py-3 text-left font-medium">Status</th>
                    <th className="px-4 py-3 text-left font-medium">Triggered At</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr
                      key={alert.id}
                      className={
                        alert.is_triggered
                          ? "border-b bg-green-50 dark:bg-green-950/30"
                          : "border-b"
                      }
                    >
                      <td className="px-4 py-3 font-medium">{alert.symbol}</td>
                      <td className="px-4 py-3">
                        {alert.direction === "above" ? "Above" : "Below"} $
                        {alert.target_price.toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        {alert.is_triggered ? (
                          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-300">
                            Triggered
                          </span>
                        ) : (
                          <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                            Active
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {formatDate(alert.triggered_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(alert.id)}
                          disabled={deleting === alert.id}
                        >
                          {deleting === alert.id ? (
                            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="mr-1.5 h-4 w-4" />
                          )}
                          Delete
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
