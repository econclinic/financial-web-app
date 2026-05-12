const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type AlertDirection = "price_above" | "price_below" | "daily_change_above" | "daily_change_below";

export interface Alert {
  id: number;
  user_id: number;
  symbol: string;
  target_price: number;
  direction: AlertDirection;
  is_triggered: boolean;
  created_at: string;
  triggered_at: string | null;
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function fetchAlerts(token: string): Promise<Alert[]> {
  const res = await fetch(`${API_BASE}/api/alerts`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<Alert[]>;
}

export async function createAlert(
  token: string,
  symbol: string,
  targetPrice: number,
  direction: AlertDirection,
): Promise<Alert> {
  const res = await fetch(`${API_BASE}/api/alerts`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      symbol,
      target_price: targetPrice,
      direction,
    }),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail ?? `Failed to create alert (${res.status})`);
  }
  return res.json() as Promise<Alert>;
}

export async function deleteAlert(
  token: string,
  alertId: number,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/alerts/${alertId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail ?? `Failed to delete alert (${res.status})`);
  }
}
