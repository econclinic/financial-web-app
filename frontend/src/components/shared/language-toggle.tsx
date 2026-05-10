"use client";

import { Globe } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useLocale } from "@/hooks/use-locale";
import { type Locale, localeConfig } from "@/lib/i18n/translations";

export function LanguageToggle() {
  const { locale, setLocale } = useLocale();

  const nextLocale: Locale = locale === "en" ? "fa" : "en";

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={() => setLocale(nextLocale)}
      aria-label={`Switch to ${localeConfig[nextLocale].label}`}
      title={localeConfig[nextLocale].label}
    >
      <Globe className="h-4 w-4" />
    </Button>
  );
}
