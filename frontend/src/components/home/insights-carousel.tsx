"use client";

import { Lightbulb, TrendingUp, AlertTriangle, BarChart3 } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";

interface InsightCard {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  titleKey: string;
  descKey: string;
  color: string;
}

const PLACEHOLDER_INSIGHTS: InsightCard[] = [
  {
    id: "diversification",
    icon: Lightbulb,
    titleKey: "home.insightDiversifyTitle",
    descKey: "home.insightDiversifyDesc",
    color: "text-blue-500",
  },
  {
    id: "top-performer",
    icon: TrendingUp,
    titleKey: "home.insightTopPerformerTitle",
    descKey: "home.insightTopPerformerDesc",
    color: "text-green-500",
  },
  {
    id: "concentration",
    icon: AlertTriangle,
    titleKey: "home.insightConcentrationTitle",
    descKey: "home.insightConcentrationDesc",
    color: "text-orange-500",
  },
  {
    id: "drawdown",
    icon: BarChart3,
    titleKey: "home.insightDrawdownTitle",
    descKey: "home.insightDrawdownDesc",
    color: "text-red-500",
  },
];

export function InsightsCarousel() {
  const { t } = useLocale();

  return (
    <section id="insights">
      <h3 className="text-base font-semibold">{t("home.insights" as never)}</h3>

      <div className="mt-3 flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2 scrollbar-none">
        {PLACEHOLDER_INSIGHTS.map((insight) => {
          const Icon = insight.icon;
          return (
            <div
              key={insight.id}
              className="flex h-[140px] min-w-[260px] shrink-0 snap-start flex-col rounded-xl border bg-card p-5 shadow-sm sm:min-w-[300px]"
            >
              <div className="flex items-center gap-2">
                <Icon className={`h-5 w-5 shrink-0 ${insight.color}`} />
                <h4 className="text-sm font-semibold">{t(insight.titleKey as never)}</h4>
              </div>
              <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-muted-foreground">
                {t(insight.descKey as never)}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
