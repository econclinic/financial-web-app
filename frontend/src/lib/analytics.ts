const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export interface SymbolPnl {
  symbol: string;
  pnl: number;
  pnl_percent: number;
  current_price: number;
  value: number;
}

export interface PortfolioOverview {
  total_value: number;
  total_cost_basis: number;
  total_pnl: number;
  today_change_value: number;
  today_change_percent: number;
  top_gainers: SymbolPnl[];
  top_losers: SymbolPnl[];
  allocation_by_asset_type: Record<string, number>;
  allocation_by_symbol: Record<string, number>;
}

export interface AllocationData {
  allocation_by_asset_type: Record<string, number>;
  allocation_by_symbol: Record<string, number>;
}

export interface HistoryPoint {
  timestamp: string;
  value: number;
}

export interface PortfolioHistory {
  range: string;
  data: HistoryPoint[];
}

export async function fetchPortfolioOverview(
  token: string,
): Promise<PortfolioOverview> {
  const res = await fetch(`${API_BASE}/api/analytics/portfolio/overview`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<PortfolioOverview>;
}

export async function fetchAllocation(
  token: string,
): Promise<AllocationData> {
  const res = await fetch(`${API_BASE}/api/analytics/portfolio/allocation`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<AllocationData>;
}

export async function fetchPortfolioHistory(
  token: string,
  range: string = "1m",
): Promise<PortfolioHistory> {
  const res = await fetch(
    `${API_BASE}/api/analytics/portfolio/history?range=${range}`,
    { headers: authHeaders(token) },
  );
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<PortfolioHistory>;
}
