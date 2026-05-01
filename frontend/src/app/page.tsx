import { BarChart3, TrendingUp, Wallet, ArrowUpRight } from "lucide-react";

import { MarketDataSection } from "@/components/shared/market-data-section";

const stats = [
  { label: "Portfolio Value", value: "$0.00", icon: Wallet },
  { label: "Today's Change", value: "+$0.00", icon: TrendingUp },
  { label: "Total Return", value: "0.00%", icon: ArrowUpRight },
  { label: "Positions", value: "0", icon: BarChart3 },
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto flex items-center justify-between px-6 py-4">
          <h1 className="text-2xl font-bold tracking-tight">Financial Dashboard</h1>
          <span className="text-sm text-muted-foreground">AI Finance WebApp</span>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="rounded-xl border bg-card p-6 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <p className="text-sm font-medium text-muted-foreground">{label}</p>
              </div>
              <p className="mt-3 text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </div>

        <MarketDataSection />
      </div>
    </main>
  );
}
