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
import { useLocale } from "@/hooks/use-locale";
import type { MarketPriceInfo, PortfolioSummary, PortfolioTransaction } from "@/lib/portfolio";
import { fetchMarketPrices, fetchPortfolioSummary, fetchTransactions } from "@/lib/portfolio";

export default function PortfolioPage() {
  const { token } = useAuth();
  const { t } = useLocale();
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
        const [s, txns] = await Promise.all([
          fetchPortfolioSummary(token!),
          fetchTransactions(token!),
        ]);
        if (cancelled) return;
        setSummary(s);
        setTransactions(txns);
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
        <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-2xl font-bold tracking-tight">{t("portfolio.title")}</h2>
            <Link href="/portfolio/new-transaction">
              <Button size="sm">
                <Plus className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                {t("portfolio.newTransaction")}
              </Button>
            </Link>
          </div>

          {loading && (
            <div className="mt-8 flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("portfolio.loading")}
            </div>
          )}

          {error && (
            <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          {priceError && (
            <div className="mt-4 rounded-xl border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-700 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-300">
              {priceError} {t("portfolio.priceError")}
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
                    {t("portfolio.noPositions")}
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
  const { t } = useLocale();
  const pnlPositive = summary.total_pnl >= 0;
  const pnlPercent = summary.pnl_percentage.toFixed(2);

  const cards = [
    {
      label: t("portfolio.totalValue"),
      value: `$${summary.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      icon: Wallet,
    },
    {
      label: t("portfolio.totalInvested"),
      value: `$${summary.total_invested.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      icon: DollarSign,
    },
    {
      label: t("portfolio.totalPnl"),
      value: `${pnlPositive ? "+" : ""}$${summary.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: pnlPositive ? "text-green-600" : "text-red-600",
    },
    {
      label: t("portfolio.return"),
      value: `${pnlPositive ? "+" : ""}${pnlPercent}%`,
      icon: pnlPositive ? ArrowUpRight : ArrowDownRight,
      color: pnlPositive ? "text-green-600" : "text-red-600",
    },
  ];

  return (
    <div className="mt-6 grid gap-3 grid-cols-2 lg:grid-cols-4 sm:gap-4">
      {cards.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="rounded-xl border bg-card p-4 shadow-sm sm:p-6">
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
  const { t } = useLocale();

  return (
    <div className="mt-6 sm:mt-8">
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">{t("portfolio.positions")}</h3>
      <div className="-mx-4 overflow-x-auto sm:mx-0 sm:rounded-xl sm:border sm:bg-card sm:shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-start font-medium">{t("portfolio.symbol")}</th>
              <th className="px-4 py-3 text-start font-medium">{t("portfolio.type")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.quantity")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.avgPrice")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.currentPrice")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.value")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.pnl")}</th>
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
                  <td className="px-4 py-3 text-end">
                    {pos.total_quantity.toLocaleString(undefined, {
                      maximumFractionDigits: 8,
                    })}
                  </td>
                  <td className="px-4 py-3 text-end">
                    ${pos.average_buy_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-end">
                    <span className="inline-flex items-center gap-1.5">
                      ${pos.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      {isLive && (
                        <span className="inline-flex items-center gap-0.5 rounded-full bg-green-100 px-1.5 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                          <Radio className="h-2.5 w-2.5" />
                          {t("portfolio.live")}
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-end font-medium">
                    ${pos.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className={`px-4 py-3 text-end font-medium ${pnlColor}`}>
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
  const { t } = useLocale();
  const chartData = summary.positions.map((pos) => ({
    symbol: pos.symbol,
    value: pos.total_value,
  }));

  const values = chartData.map((d) => d.value);
  const maxValue = Math.max(...values);
  const padding = maxValue * 0.1 || 1;

  return (
    <div className="mt-6 sm:mt-8">
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">{t("portfolio.allocation")}</h3>
      <div className="rounded-xl border bg-card p-4 shadow-sm sm:p-6">
        <div className="h-[220px] w-full sm:h-[300px] lg:h-[380px]">
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
                    t("portfolio.value"),
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
  const { t } = useLocale();

  return (
    <div className="mt-6 sm:mt-8">
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">{t("portfolio.transactionHistory")}</h3>
      <div className="-mx-4 overflow-x-auto sm:mx-0 sm:rounded-xl sm:border sm:bg-card sm:shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-start font-medium">{t("portfolio.date")}</th>
              <th className="px-4 py-3 text-start font-medium">{t("portfolio.symbol")}</th>
              <th className="px-4 py-3 text-start font-medium">{t("portfolio.type")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.quantity")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.price")}</th>
              <th className="px-4 py-3 text-end font-medium">{t("portfolio.total")}</th>
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
                  <td className="px-4 py-3 text-end">
                    {txn.quantity.toLocaleString(undefined, {
                      maximumFractionDigits: 8,
                    })}
                  </td>
                  <td className="px-4 py-3 text-end">
                    ${txn.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-end font-medium">
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
