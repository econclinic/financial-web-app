"use client";

import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { BannerSlider } from "@/components/home/banner-slider";
import { PortfolioOverviewCard } from "@/components/home/portfolio-overview-card";
import { AllocationDonut } from "@/components/home/allocation-donut";
import { LiveMarketPrices } from "@/components/home/live-market-prices";
import { InsightsCarousel } from "@/components/home/insights-carousel";
import { VideoSection } from "@/components/home/video-section";
import { ArticleCarousel } from "@/components/home/article-carousel";
import { usePortfolioPerformance } from "@/hooks/use-portfolio-performance";
import { usePortfolioAllocation } from "@/hooks/use-portfolio-allocation";

export default function DashboardPage() {
  const performance = usePortfolioPerformance("7d");
  const allocation = usePortfolioAllocation();

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />

        <div className="container mx-auto space-y-6 px-4 py-6 sm:px-6 sm:py-8">
          <BannerSlider />

          <div className="grid gap-6 md:grid-cols-2">
            <PortfolioOverviewCard
              data={performance.data}
              loading={performance.loading}
              error={performance.error}
            />
            <AllocationDonut
              data={allocation.data}
              loading={allocation.loading}
              error={allocation.error}
            />
          </div>

          <LiveMarketPrices />

          <InsightsCarousel />

          <VideoSection />

          <ArticleCarousel />
        </div>
      </main>
    </ProtectedRoute>
  );
}
