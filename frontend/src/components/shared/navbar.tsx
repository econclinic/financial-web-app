"use client";

import Link from "next/link";
import { Bell, Briefcase, Eye, LogIn, LogOut, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export function Navbar() {
  const { user, logout } = useAuth();

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
