"use client";

import {
  createContext,
  useCallback,
  useContext,
  useSyncExternalStore,
} from "react";

import {
  type Locale,
  type TranslationKey,
  localeConfig,
  t,
} from "@/lib/i18n/translations";

interface LocaleContextValue {
  locale: Locale;
  dir: "ltr" | "rtl";
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, params?: Record<string, string>) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

const STORAGE_KEY = "app-locale";

let currentLocale: Locale = "en";

function getSnapshot(): Locale {
  return currentLocale;
}

function getServerSnapshot(): Locale {
  return "en";
}

const listeners = new Set<() => void>();

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function applyLocale(locale: Locale) {
  currentLocale = locale;
  const { dir } = localeConfig[locale];
  const root = document.documentElement;
  root.setAttribute("lang", locale);
  root.setAttribute("dir", dir);
  localStorage.setItem(STORAGE_KEY, locale);
  listeners.forEach((cb) => cb());
}

if (typeof window !== "undefined") {
  const stored = localStorage.getItem(STORAGE_KEY) as Locale | null;
  currentLocale = stored === "en" || stored === "fa" ? stored : "en";
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const dir = localeConfig[locale].dir;

  const setLocale = useCallback((l: Locale) => applyLocale(l), []);
  const translate = useCallback(
    (key: TranslationKey, params?: Record<string, string>) => t(locale, key, params),
    [locale],
  );

  return (
    <LocaleContext value={{ locale, dir, setLocale, t: translate }}>
      {children}
    </LocaleContext>
  );
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used within LocaleProvider");
  return ctx;
}
