"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BarChart3, Bell, BellRing, Briefcase, Eye, LogIn, LogOut, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { fetchUnreadCount } from "@/lib/notifications";

export function Navbar() {
  const { user, token, logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);

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

  return (
    <header className="border-b">
      <div className="container mx-auto flex items-center justify-between px-6 py-4">
        <h1 className="text-2xl font-bold tracking-tight">Financial Dashboard</h1>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link href="/portfolio">
                <Button variant="outline" size="sm">
                  <Briefcase className="mr-1.5 h-4 w-4" />
                  Portfolio
                </Button>
              </Link>
              <Link href="/dashboard/analytics">
                <Button variant="outline" size="sm">
                  <BarChart3 className="mr-1.5 h-4 w-4" />
                  Analytics
                </Button>
              </Link>
              <Link href="/watchlist">
                <Button variant="outline" size="sm">
                  <Eye className="mr-1.5 h-4 w-4" />
                  Watchlist
                </Button>
              </Link>
              <Link href="/alerts">
                <Button variant="outline" size="sm">
                  <Bell className="mr-1.5 h-4 w-4" />
                  Alerts
                </Button>
              </Link>
              <Link href="/notifications">
                <Button variant="outline" size="sm" className="relative">
                  {unreadCount > 0 ? (
                    <BellRing className="mr-1.5 h-4 w-4" />
                  ) : (
                    <Bell className="mr-1.5 h-4 w-4" />
                  )}
                  Notifications
                  {unreadCount > 0 && (
                    <span className="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </Button>
              </Link>
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <Button variant="outline" size="sm" onClick={logout}>
                <LogOut className="mr-1.5 h-4 w-4" />
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="outline" size="sm">
                  <LogIn className="mr-1.5 h-4 w-4" />
                  Login
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm">
                  <UserPlus className="mr-1.5 h-4 w-4" />
                  Register
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
