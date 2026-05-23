"use client";

import { BookOpen } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";

interface Article {
  id: string;
  titleKey: string;
  summaryKey: string;
  href: string;
  color: string;
}

const PLACEHOLDER_ARTICLES: Article[] = [
  {
    id: "portfolio-basics",
    titleKey: "home.articleBasicsTitle",
    summaryKey: "home.articleBasicsDesc",
    href: "https://www.investopedia.com/terms/p/portfolio.asp",
    color: "from-blue-500/20 to-blue-600/10",
  },
  {
    id: "diversification",
    titleKey: "home.articleDiversifyTitle",
    summaryKey: "home.articleDiversifyDesc",
    href: "https://www.investopedia.com/terms/d/diversification.asp",
    color: "from-green-500/20 to-green-600/10",
  },
  {
    id: "risk-management",
    titleKey: "home.articleRiskTitle",
    summaryKey: "home.articleRiskDesc",
    href: "https://www.investopedia.com/terms/r/riskmanagement.asp",
    color: "from-orange-500/20 to-orange-600/10",
  },
  {
    id: "market-analysis",
    titleKey: "home.articleMarketTitle",
    summaryKey: "home.articleMarketDesc",
    href: "https://www.investopedia.com/terms/m/market-analysis.asp",
    color: "from-purple-500/20 to-purple-600/10",
  },
];

export function ArticleCarousel() {
  const { t } = useLocale();

  return (
    <section id="articles" className="min-w-0 overflow-hidden">
      <h3 className="text-base font-semibold">{t("home.articles" as never)}</h3>

      <div className="mt-3 flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2 scrollbar-none">
        {PLACEHOLDER_ARTICLES.map((article) => (
          <a
            key={article.id}
            href={article.href}
            target="_blank"
            rel="noopener noreferrer"
            className="min-w-[260px] shrink-0 snap-start overflow-hidden rounded-xl border bg-card shadow-sm transition-shadow hover:shadow-md sm:min-w-[300px]"
          >
            <div className={`h-28 bg-gradient-to-br ${article.color} flex items-center justify-center`}>
              <BookOpen className="h-10 w-10 text-muted-foreground/40" />
            </div>
            <div className="p-4">
              <h4 className="text-sm font-semibold line-clamp-2">{t(article.titleKey as never)}</h4>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground line-clamp-3">
                {t(article.summaryKey as never)}
              </p>
              <span className="mt-3 inline-block text-xs font-medium text-primary">
                {t("home.readMore" as never)}
              </span>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
