const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface WatchlistItem {
  id: number;
  user_id: number;
  symbol: string;
  created_at: string;
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function fetchWatchlist(
  token: string,
): Promise<WatchlistItem[]> {
  const res = await fetch(`${API_BASE}/api/watchlist`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<WatchlistItem[]>;
}

export async function addToWatchlist(
  token: string,
  symbol: string,
): Promise<WatchlistItem> {
  const res = await fetch(`${API_BASE}/api/watchlist`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ symbol }),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail ?? `Failed to add symbol (${res.status})`);
  }
  return res.json() as Promise<WatchlistItem>;
}

export async function removeFromWatchlist(
  token: string,
  symbol: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail ?? `Failed to remove symbol (${res.status})`);
  }
}
