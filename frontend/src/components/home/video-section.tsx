"use client";

import { Play } from "lucide-react";

import { useLocale } from "@/hooks/use-locale";

const FEATURED_VIDEO = {
  id: "dQw4w9WgXcQ",
  titleKey: "home.videoTitle",
  descKey: "home.videoDesc",
};

export function VideoSection() {
  const { t } = useLocale();

  return (
    <section id="education" className="rounded-xl border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <Play className="h-5 w-5 text-primary" />
        <h3 className="text-base font-semibold">{t("home.education" as never)}</h3>
      </div>

      <div className="relative mt-4 overflow-hidden rounded-lg" style={{ paddingBottom: "56.25%" }}>
        <iframe
          className="absolute inset-0 h-full w-full"
          src={`https://www.youtube.com/embed/${FEATURED_VIDEO.id}`}
          title={t(FEATURED_VIDEO.titleKey as never)}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>

      <h4 className="mt-4 text-sm font-semibold">{t(FEATURED_VIDEO.titleKey as never)}</h4>
      <p className="mt-1 text-sm text-muted-foreground">{t(FEATURED_VIDEO.descKey as never)}</p>
    </section>
  );
}
