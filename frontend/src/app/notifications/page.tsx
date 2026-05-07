"use client";

import { useEffect, useState } from "react";
import { Bell, CheckCheck, Loader2, Mail, MailOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useAuth } from "@/hooks/use-auth";
import type { Notification } from "@/lib/notifications";
import {
  fetchNotifications,
  markAllNotificationsAsRead,
  markNotificationAsRead,
} from "@/lib/notifications";

export default function NotificationsPage() {
  const { token } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);
  const [markingId, setMarkingId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function load() {
      try {
        const list = await fetchNotifications(token!);
        if (cancelled) return;
        setNotifications(list);
      } catch (err: unknown) {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to load notifications",
        );
      }
      if (!cancelled) setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [token, refreshKey]);

  async function handleMarkAsRead(id: number) {
    if (!token) return;
    setMarkingId(id);
    try {
      await markNotificationAsRead(token, id);
      setRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to mark as read",
      );
    } finally {
      setMarkingId(null);
    }
  }

  async function handleMarkAllAsRead() {
    if (!token) return;
    setMarkingAll(true);
    try {
      await markAllNotificationsAsRead(token);
      setRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to mark all as read",
      );
    } finally {
      setMarkingAll(false);
    }
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
  }

  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-6 w-6" />
              <h2 className="text-2xl font-bold tracking-tight">
                Notifications
              </h2>
            </div>
            {hasUnread && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkAllAsRead}
                disabled={markingAll}
              >
                {markingAll ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <CheckCheck className="mr-1.5 h-4 w-4" />
                )}
                Mark all as read
              </Button>
            )}
          </div>

          {/* Loading state */}
          {loading && (
            <div className="mt-8 flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading notifications...
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && notifications.length === 0 && (
            <div className="mt-8 rounded-xl border bg-muted/40 p-8 text-center text-muted-foreground">
              <Bell className="mx-auto h-8 w-8 mb-2" />
              <p>No notifications.</p>
              <p className="text-sm mt-1">
                Notifications will appear here when your price alerts are
                triggered.
              </p>
            </div>
          )}

          {/* Notifications list */}
          {!loading && notifications.length > 0 && (
            <div className="mt-6 space-y-3">
              {notifications.map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start justify-between gap-4 rounded-xl border p-4 ${
                    n.is_read
                      ? "bg-background"
                      : "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/30"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {n.is_read ? (
                      <MailOpen className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    ) : (
                      <Mail className="mt-0.5 h-5 w-5 text-blue-600 dark:text-blue-400" />
                    )}
                    <div>
                      <p className="font-medium">{n.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {n.message}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDate(n.created_at)}
                      </p>
                    </div>
                  </div>
                  {!n.is_read && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleMarkAsRead(n.id)}
                      disabled={markingId === n.id}
                    >
                      {markingId === n.id ? (
                        <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                      ) : (
                        <MailOpen className="mr-1.5 h-4 w-4" />
                      )}
                      Mark as read
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
