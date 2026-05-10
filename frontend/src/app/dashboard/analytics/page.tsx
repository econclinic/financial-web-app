"use client";

import { useEffect, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  DollarSign,
  Loader2,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import {
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useAuth } from "@/hooks/use-auth";
import { useLocale } from "@/hooks/use-locale";
import type {
  PortfolioOverview,
  PortfolioHistory,
  SymbolPnl,
} from "@/lib/analytics";
import {
  fetchPortfolioOverview,
  fetchPortfolioHistory,
} from "@/lib/analytics";

const RANGE_OPTIONS = ["1m", "3m", "6m", "1y", "all"] as const;
const PIE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

function fmt(n: number): string {
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function AnalyticsPage() {
  const { token } = useAuth();
  const { t } = useLocale();
  const [overview, setOverview] = useState<PortfolioOverview | null>(null);
  const [history, setHistory] = useState<PortfolioHistory | null>(null);
  const [selectedRange, setSelectedRange] = useState<string>("1m");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function load() {
      try {
        const ov = await fetchPortfolioOverview(token!);
        if (cancelled) return;
        setOverview(ov);
      } catch (err: unknown) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      }
      if (!cancelled) setLoading(false);
    }

    load();
    return () => { cancelled = true; };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function loadHistory() {
      try {
        const h = await fetchPortfolioHistory(token!, selectedRange);
        if (!cancelled) setHistory(h);
      } catch {
        /* ignore history errors */
      }
    }

    loadHistory();
    return () => { cancelled = true; };
  }, [token, selectedRange]);

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8">
          <h2 className="text-2xl font-bold tracking-tight">{t("analytics.title")}</h2>

          {loading && (
            <div className="mt-8 flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("analytics.loading")}
            </div>
          )}

          {error && (
            <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          {!loading && !error && overview && (
            <>
              <OverviewCards overview={overview} />
              <div className="mt-6 grid gap-4 sm:mt-8 sm:gap-8 lg:grid-cols-2">
                <AllocationChart
                  title={t("analytics.allocationByClass")}
                  data={overview.allocation_by_asset_type}
                />
                <AllocationChart
                  title={t("analytics.allocationBySymbol")}
                  data={overview.allocation_by_symbol}
                />
              </div>
              <PerformanceChart
                history={history}
                selectedRange={selectedRange}
                onRangeChange={setSelectedRange}
              />
              <TopMovers
                gainers={overview.top_gainers}
                losers={overview.top_losers}
              />
            </>
          )}

          {!loading && !error && overview && overview.total_value === 0 && (
            <div className="mt-8 rounded-xl border bg-card p-8 text-center shadow-sm">
              <p className="text-muted-foreground">
                {t("analytics.noData")}
              </p>
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}

function OverviewCards({ overview }: { overview: PortfolioOverview }) {
  const { t } = useLocale();
  const pnlPositive = overview.total_pnl >= 0;
  const todayPositive = overview.today_change_value >= 0;

  const cards = [
    {
      label: t("analytics.totalValue"),
      value: `$${fmt(overview.total_value)}`,
      icon: Wallet,
      color: "text-blue-500",
    },
    {
      label: t("analytics.todaysChange"),
      value: `${todayPositive ? "+" : ""}$${fmt(overview.today_change_value)}`,
      sub: `${todayPositive ? "+" : ""}${overview.today_change_percent.toFixed(2)}%`,
      icon: todayPositive ? ArrowUpRight : ArrowDownRight,
      color: todayPositive ? "text-green-500" : "text-red-500",
    },
    {
      label: t("analytics.totalPnl"),
      value: `${pnlPositive ? "+" : ""}$${fmt(overview.total_pnl)}`,
      icon: pnlPositive ? TrendingUp : TrendingDown,
      color: pnlPositive ? "text-green-500" : "text-red-500",
    },
    {
      label: t("analytics.costBasis"),
      value: `$${fmt(overview.total_cost_basis)}`,
      icon: DollarSign,
      color: "text-gray-500",
    },
  ];

  return (
    <div className="mt-6 grid gap-3 grid-cols-2 lg:grid-cols-4 sm:gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-xl border bg-card p-5 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">{c.label}</p>
            <c.icon className={`h-5 w-5 ${c.color}`} />
          </div>
          <p className="mt-2 text-2xl font-bold">{c.value}</p>
          {c.sub && <p className={`mt-1 text-sm ${c.color}`}>{c.sub}</p>}
        </div>
      ))}
    </div>
  );
}

function AllocationChart({
  title,
  data,
}: {
  title: string;
  data: Record<string, number>;
}) {
  const entries = Object.entries(data);
  if (entries.length === 0) return null;

  const chartData = entries.map(([name, value]) => ({ name, value }));

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      <div className="h-[250px] w-full sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={90}
              dataKey="value"
              nameKey="name"
              label={({ name, value }) => `${name} ${value}%`}
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v) => `${v}%`} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function PerformanceChart({
  history,
  selectedRange,
  onRangeChange,
}: {
  history: PortfolioHistory | null;
  selectedRange: string;
  onRangeChange: (r: string) => void;
}) {
  const { t } = useLocale();
  const chartData = (history?.data ?? []).map((p) => ({
    date: new Date(p.timestamp).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    }),
    value: p.value,
  }));

  return (
    <div className="mt-8 rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-base font-semibold sm:text-lg">
          <BarChart3 className="inline h-5 w-5 ltr:mr-2 rtl:ml-2" />
          {t("analytics.performance")}
        </h3>
        <div className="flex flex-wrap gap-1">
          {RANGE_OPTIONS.map((r) => (
            <button
              key={r}
              onClick={() => onRangeChange(r)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                selectedRange === r
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      {chartData.length > 0 ? (
        <div className="h-[220px] w-full sm:h-[300px] lg:h-[380px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                formatter={(v) => [`$${fmt(Number(v))}`, t("analytics.totalValue")]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="py-12 text-center text-muted-foreground">
          {t("analytics.noHistory")}
        </p>
      )}
    </div>
  );
}

function TopMovers({
  gainers,
  losers,
}: {
  gainers: SymbolPnl[];
  losers: SymbolPnl[];
}) {
  const { t } = useLocale();
  if (gainers.length === 0 && losers.length === 0) return null;

  return (
    <div className="mt-6 grid gap-4 sm:mt-8 sm:gap-8 md:grid-cols-2">
      <MoverList title={t("analytics.topGainers")} items={gainers} positive />
      <MoverList title={t("analytics.topLosers")} items={losers} positive={false} />
    </div>
  );
}

function MoverList({
  title,
  items,
  positive,
}: {
  title: string;
  items: SymbolPnl[];
  positive: boolean;
}) {
  if (items.length === 0) return null;

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold">
        {positive ? (
          <TrendingUp className="inline h-5 w-5 text-green-500 ltr:mr-2 rtl:ml-2" />
        ) : (
          <TrendingDown className="inline h-5 w-5 text-red-500 ltr:mr-2 rtl:ml-2" />
        )}
        {title}
      </h3>
      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.symbol}
            className="flex items-center justify-between rounded-lg p-3 transition-colors hover:bg-muted"
          >
            <div>
              <p className="font-semibold">{item.symbol}</p>
              <p className="text-sm text-muted-foreground">
                ${fmt(item.current_price)}
              </p>
            </div>
            <div className="text-end">
              <p className="font-semibold">${fmt(item.value)}</p>
              <p
                className={`text-sm font-medium ${
                  positive ? "text-green-500" : "text-red-500"
                }`}
              >
                {positive ? "+" : ""}
                {item.pnl_percent.toFixed(2)}%
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
