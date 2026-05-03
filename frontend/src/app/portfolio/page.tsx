"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  DollarSign,
  Loader2,
  Plus,
  Radio,
  TrendingUp,
  Wallet,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useAuth } from "@/hooks/use-auth";
import type { MarketPriceInfo, PortfolioSummary, PortfolioTransaction } from "@/lib/portfolio";
import { fetchMarketPrices, fetchPortfolioSummary, fetchTransactions } from "@/lib/portfolio";

export default function PortfolioPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [transactions, setTransactions] = useState<PortfolioTransaction[]>([]);
  const [livePrices, setLivePrices] = useState<Record<string, MarketPriceInfo> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [priceError, setPriceError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function loadData() {
      try {
        const [s, t] = await Promise.all([
          fetchPortfolioSummary(token!),
          fetchTransactions(token!),
        ]);
        if (cancelled) return;
        setSummary(s);
        setTransactions(t);
      } catch (err: unknown) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load portfolio");
      }

      try {
        const prices = await fetchMarketPrices(token!, ["BTC", "ETH"]);
        if (cancelled) return;
        setLivePrices(prices);
      } catch (err: unknown) {
        if (cancelled) return;
        setPriceError(err instanceof Error ? err.message : "Live prices unavailable");
      }

      if (!cancelled) setLoading(false);
    }

    loadData();
    return () => { cancelled = true; };
  }, [token]);

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold tracking-tight">Portfolio</h2>
            <Link href="/portfolio/new-transaction">
              <Button size="sm">
                <Plus className="mr-1.5 h-4 w-4" />
                New Transaction
              </Button>
            </Link>
          </div>

          {loading && (
            <div className="mt-8 flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading portfolio...
            </div>
          )}

          {error && (
            <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          {priceError && (
            <div className="mt-4 rounded-xl border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-700 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-300">
              {priceError} — showing last cached prices.
            </div>
          )}

          {!loading && !error && summary && (
            <>
              <SummaryCards summary={summary} />
              {summary.positions.length > 0 && (
                <>
                  <PositionsTable summary={summary} livePrices={livePrices} />
                  <PortfolioChart summary={summary} />
                </>
              )}
              {summary.positions.length === 0 && (
                <div className="mt-8 rounded-xl border bg-card p-8 text-center shadow-sm">
                  <p className="text-muted-foreground">
                    No positions yet. Add your first transaction to get started.
                  </p>
                </div>
              )}
              {transactions.length > 0 && (
                <TransactionHistory transactions={transactions} />
              )}
            </>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}

function SummaryCards({ summary }: { summary: PortfolioSummary }) {
  const pnlPositive = summary.total_pnl >= 0;
  const pnlPercent = summary.pnl_percentage.toFixed(2);

  const cards = [
    {
      label: "Total Value",
      value: `$${summary.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      icon: Wallet,
    },
    {
      label: "Total Invested",
      value: `$${summary.total_invested.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      icon: DollarSign,
    },
    {
      label: "Total P&L",
      value: `${pnlPositive ? "+" : ""}$${summary.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: pnlPositive ? "text-green-600" : "text-red-600",
    },
    {
      label: "Return",
      value: `${pnlPositive ? "+" : ""}${pnlPercent}%`,
      icon: pnlPositive ? ArrowUpRight : ArrowDownRight,
      color: pnlPositive ? "text-green-600" : "text-red-600",
    },
  ];

  return (
    <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
          </div>
          <p className={`mt-3 text-2xl font-semibold ${color ?? ""}`}>{value}</p>
        </div>
      ))}
    </div>
  );
}

function PositionsTable({
  summary,
  livePrices,
}: {
  summary: PortfolioSummary;
  livePrices: Record<string, MarketPriceInfo> | null;
}) {
  return (
    <div className="mt-8">
      <h3 className="mb-4 text-lg font-semibold">Positions</h3>
      <div className="overflow-x-auto rounded-xl border bg-card shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Symbol</th>
              <th className="px-4 py-3 text-left font-medium">Type</th>
              <th className="px-4 py-3 text-right font-medium">Quantity</th>
              <th className="px-4 py-3 text-right font-medium">Avg Price</th>
              <th className="px-4 py-3 text-right font-medium">Current Price</th>
              <th className="px-4 py-3 text-right font-medium">Value</th>
              <th className="px-4 py-3 text-right font-medium">P&L</th>
            </tr>
          </thead>
          <tbody>
            {summary.positions.map((pos) => {
              const pnlColor =
                pos.unrealized_pnl >= 0 ? "text-green-600" : "text-red-600";
              const isLive = livePrices !== null && pos.symbol in livePrices;
              return (
                <tr key={pos.symbol} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{pos.symbol}</td>
                  <td className="px-4 py-3 capitalize text-muted-foreground">
                    {pos.asset_type}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {pos.total_quantity.toLocaleString(undefined, {
                      maximumFractionDigits: 8,
                    })}
                  </td>
                  <td className="px-4 py-3 text-right">
                    ${pos.average_buy_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1.5">
                      ${pos.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      {isLive && (
                        <span className="inline-flex items-center gap-0.5 rounded-full bg-green-100 px-1.5 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                          <Radio className="h-2.5 w-2.5" />
                          Live
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium">
                    ${pos.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className={`px-4 py-3 text-right font-medium ${pnlColor}`}>
                    {pos.unrealized_pnl >= 0 ? "+" : ""}
                    ${pos.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PortfolioChart({ summary }: { summary: PortfolioSummary }) {
  const chartData = summary.positions.map((pos) => ({
    symbol: pos.symbol,
    value: pos.total_value,
  }));

  const values = chartData.map((d) => d.value);
  const maxValue = Math.max(...values);
  const padding = maxValue * 0.1 || 1;

  return (
    <div className="mt-8">
      <h3 className="mb-4 text-lg font-semibold">Portfolio Allocation</h3>
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="symbol"
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
                tickLine={false}
              />
              <YAxis
                domain={[0, maxValue + padding]}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
                tickFormatter={(v: number) => `$${v.toLocaleString()}`}
                tickLine={false}
              />
              <Tooltip
                formatter={(value) => {
                  const num = Number(value);
                  return [
                    `$${num.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
                    "Value",
                  ];
                }}
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ r: 5 }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function TransactionHistory({
  transactions,
}: {
  transactions: PortfolioTransaction[];
}) {
  return (
    <div className="mt-8">
      <h3 className="mb-4 text-lg font-semibold">Transaction History</h3>
      <div className="overflow-x-auto rounded-xl border bg-card shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Date</th>
              <th className="px-4 py-3 text-left font-medium">Symbol</th>
              <th className="px-4 py-3 text-left font-medium">Type</th>
              <th className="px-4 py-3 text-right font-medium">Quantity</th>
              <th className="px-4 py-3 text-right font-medium">Price</th>
              <th className="px-4 py-3 text-right font-medium">Total</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => {
              const isBuy = txn.transaction_type === "buy";
              return (
                <tr key={txn.id} className="border-b last:border-0">
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(txn.timestamp).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </td>
                  <td className="px-4 py-3 font-medium">{txn.symbol}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        isBuy
                          ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                          : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                      }`}
                    >
                      {txn.transaction_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {txn.quantity.toLocaleString(undefined, {
                      maximumFractionDigits: 8,
                    })}
                  </td>
                  <td className="px-4 py-3 text-right">
                    ${txn.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-right font-medium">
                    ${(txn.quantity * txn.price).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
