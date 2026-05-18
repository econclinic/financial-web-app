"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/hooks/use-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface AllocationAsset {
  symbol: string;
  quantity: number;
  price: number;
  value: number;
  weight: number | null;
}

export interface AllocationData {
  total_value: number;
  assets: AllocationAsset[];
}

export function usePortfolioAllocation() {
  const { token } = useAuth();
  const [data, setData] = useState<AllocationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    fetch(`${API_BASE}/api/portfolio/allocation`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json() as Promise<AllocationData>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load allocation");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, refreshKey]);

  function refetch() {
    setRefreshKey((k) => k + 1);
  }

  return { data, loading, error, refetch };
}
