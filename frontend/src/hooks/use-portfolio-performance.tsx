"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/hooks/use-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface PerformanceSummary {
  range: string;
  start_timestamp: string | null;
  end_timestamp: string | null;
  starting_value: number;
  ending_value: number;
  absolute_return: number;
  total_return: number;
  total_return_pct: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  snapshot_count: number;
}

export function usePortfolioPerformance(range: string = "7d") {
  const { token } = useAuth();
  const [data, setData] = useState<PerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    fetch(`${API_BASE}/api/portfolio/performance?range=${range}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json() as Promise<PerformanceSummary>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load performance");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, range, refreshKey]);

  function refetch() {
    setRefreshKey((k) => k + 1);
  }

  return { data, loading, error, refetch };
}
