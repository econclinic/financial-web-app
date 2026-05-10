"use client";

import { BarChart3, TrendingUp, Wallet, ArrowUpRight } from "lucide-react";

import { MarketDataSection } from "@/components/shared/market-data-section";
import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useLocale } from "@/hooks/use-locale";
import type { TranslationKey } from "@/lib/i18n/translations";

const stats: { labelKey: TranslationKey; value: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { labelKey: "dashboard.portfolioValue", value: "$0.00", icon: Wallet },
  { labelKey: "dashboard.todaysChange", value: "+$0.00", icon: TrendingUp },
  { labelKey: "dashboard.totalReturn", value: "0.00%", icon: ArrowUpRight },
  { labelKey: "dashboard.positions", value: "0", icon: BarChart3 },
];

export default function DashboardPage() {
  const { t } = useLocale();

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />

        <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map(({ labelKey, value, icon: Icon }) => (
              <div
                key={labelKey}
                className="rounded-xl border bg-card p-6 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <p className="text-sm font-medium text-muted-foreground">{t(labelKey)}</p>
                </div>
                <p className="mt-3 text-2xl font-semibold">{value}</p>
              </div>
            ))}
          </div>

          <MarketDataSection />
        </div>
      </main>
    </ProtectedRoute>
  );
}
