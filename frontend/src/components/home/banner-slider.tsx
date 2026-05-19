"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";

interface Banner {
  id: string;
  title: string;
  subtitle: string;
  gradient: string;
  href: string;
}

const BANNERS: Banner[] = [
  {
    id: "learn-investing",
    title: "home.bannerLearnTitle",
    subtitle: "home.bannerLearnSubtitle",
    gradient: "from-blue-600 to-indigo-700",
    href: "#education",
  },
  {
    id: "portfolio-insights",
    title: "home.bannerInsightsTitle",
    subtitle: "home.bannerInsightsSubtitle",
    gradient: "from-emerald-600 to-teal-700",
    href: "#insights",
  },
  {
    id: "market-watch",
    title: "home.bannerMarketTitle",
    subtitle: "home.bannerMarketSubtitle",
    gradient: "from-orange-500 to-red-600",
    href: "#market-prices",
  },
];

const AUTO_ADVANCE_MS = 5000;

export function BannerSlider() {
  const { t } = useLocale();
  const [current, setCurrent] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function startTimer() {
    stopTimer();
    timerRef.current = setInterval(() => {
      setCurrent((prev) => (prev + 1) % BANNERS.length);
    }, AUTO_ADVANCE_MS);
  }

  function stopTimer() {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  useEffect(() => {
    startTimer();
    return stopTimer;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function go(index: number) {
    setCurrent(index);
    startTimer();
  }

  function prev() {
    go((current - 1 + BANNERS.length) % BANNERS.length);
  }

  function next() {
    go((current + 1) % BANNERS.length);
  }

  const banner = BANNERS[current];

  return (
    <section id="banners" className="relative">
      <a
        href={banner.href}
        className={`flex flex-col items-center justify-center rounded-2xl bg-gradient-to-r ${banner.gradient} px-6 py-16 text-center text-white shadow-lg transition-all duration-500 sm:py-14`}
      >
        <h2 className="text-xl font-bold sm:text-2xl">{t(banner.title as never)}</h2>
        <p className="mt-2 text-sm opacity-90 sm:text-base">{t(banner.subtitle as never)}</p>
      </a>

      <button
        onClick={prev}
        className="absolute top-1/2 -translate-y-1/2 rounded-full bg-white/20 p-1.5 text-white backdrop-blur-sm transition hover:bg-white/30 ltr:left-2 rtl:right-2"
        aria-label="Previous banner"
      >
        <ChevronLeft className="h-5 w-5 rtl:rotate-180" />
      </button>
      <button
        onClick={next}
        className="absolute top-1/2 -translate-y-1/2 rounded-full bg-white/20 p-1.5 text-white backdrop-blur-sm transition hover:bg-white/30 ltr:right-2 rtl:left-2"
        aria-label="Next banner"
      >
        <ChevronRight className="h-5 w-5 rtl:rotate-180" />
      </button>

      <div className="mt-3 flex justify-center gap-2">
        {BANNERS.map((b, i) => (
          <button
            key={b.id}
            onClick={() => go(i)}
            className={`h-2 rounded-full transition-all ${
              i === current ? "w-6 bg-primary" : "w-2 bg-muted-foreground/30"
            }`}
            aria-label={`Go to banner ${i + 1}`}
          />
        ))}
      </div>
    </section>
  );
}
