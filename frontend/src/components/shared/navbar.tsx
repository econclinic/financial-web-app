"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  BarChart3,
  Bell,
  BellRing,
  Briefcase,
  Eye,
  LogIn,
  LogOut,
  Menu,
  UserPlus,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { LanguageToggle } from "@/components/shared/language-toggle";
import { useAuth } from "@/hooks/use-auth";
import { useLocale } from "@/hooks/use-locale";
import { fetchUnreadCount } from "@/lib/notifications";

export function Navbar() {
  const { user, token, logout } = useAuth();
  const { t } = useLocale();
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function poll() {
      try {
        const count = await fetchUnreadCount(token!);
        if (!cancelled) setUnreadCount(count);
      } catch {
        /* ignore */
      }
    }

    poll();
    const interval = setInterval(poll, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token]);

  const navLinks = user
    ? [
        { href: "/portfolio", label: t("nav.portfolio"), icon: Briefcase },
        { href: "/dashboard/analytics", label: t("nav.analytics"), icon: BarChart3 },
        { href: "/watchlist", label: t("nav.watchlist"), icon: Eye },
        { href: "/alerts", label: t("nav.alerts"), icon: Bell },
      ]
    : [];

  return (
    <header className="border-b">
      <div className="container mx-auto flex items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
        <Link href="/" className="shrink-0">
          <h1 className="text-lg font-bold tracking-tight sm:text-2xl">
            {t("nav.title")}
          </h1>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-2 md:flex lg:gap-3">
          {user ? (
            <>
              {navLinks.map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href}>
                  <Button variant="outline" size="sm">
                    <Icon className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                    {label}
                  </Button>
                </Link>
              ))}
              <Link href="/notifications">
                <Button variant="outline" size="sm" className="relative">
                  {unreadCount > 0 ? (
                    <BellRing className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                  ) : (
                    <Bell className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                  )}
                  {t("nav.notifications")}
                  {unreadCount > 0 && (
                    <span className="absolute -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white ltr:-right-1.5 rtl:-left-1.5">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </Button>
              </Link>
              <LanguageToggle />
              <ThemeToggle />
              <span className="hidden text-sm text-muted-foreground lg:inline">
                {user.email}
              </span>
              <Button variant="outline" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                {t("nav.logout")}
              </Button>
            </>
          ) : (
            <>
              <LanguageToggle />
              <ThemeToggle />
              <Link href="/login">
                <Button variant="outline" size="sm">
                  <LogIn className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                  {t("nav.login")}
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm">
                  <UserPlus className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                  {t("nav.register")}
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile controls */}
        <div className="flex items-center gap-2 md:hidden">
          <LanguageToggle />
          <ThemeToggle />
          {user && (
            <Link href="/notifications" className="relative">
              <Button variant="outline" size="icon">
                {unreadCount > 0 ? (
                  <BellRing className="h-4 w-4" />
                ) : (
                  <Bell className="h-4 w-4" />
                )}
              </Button>
              {unreadCount > 0 && (
                <span className="absolute -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-0.5 text-[9px] font-bold text-white ltr:-right-1 rtl:-left-1">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </Link>
          )}
          <Button
            variant="outline"
            size="icon"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t bg-background px-4 pb-4 pt-2 md:hidden">
          <nav className="flex flex-col gap-1">
            {user ? (
              <>
                {navLinks.map(({ href, label, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors hover:bg-accent"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    {label}
                  </Link>
                ))}
                <Link
                  href="/notifications"
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors hover:bg-accent"
                >
                  <Bell className="h-4 w-4 text-muted-foreground" />
                  {t("nav.notifications")}
                  {unreadCount > 0 && (
                    <span className="ms-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </Link>
                <div className="my-1 border-t" />
                <div className="flex items-center justify-between px-3 py-2">
                  <span className="text-sm text-muted-foreground">
                    {user.email}
                  </span>
                  <Button variant="outline" size="sm" onClick={logout}>
                    <LogOut className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                    {t("nav.logout")}
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-1">
                <Link href="/login" onClick={() => setMobileOpen(false)}>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <LogIn className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                    {t("nav.login")}
                  </Button>
                </Link>
                <Link href="/register" onClick={() => setMobileOpen(false)}>
                  <Button size="sm" className="w-full justify-start">
                    <UserPlus className="h-4 w-4 ltr:mr-1.5 rtl:ml-1.5" />
                    {t("nav.register")}
                  </Button>
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
