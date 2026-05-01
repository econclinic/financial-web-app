const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface MarketQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  updated_at: string;
}

export interface PricePoint {
  timestamp: string;
  price: number;
}

export interface MarketDataHistoryResponse {
  symbol: string;
  name: string;
  history: PricePoint[];
}

export async function fetchLatestQuotes(): Promise<MarketQuote[]> {
  const res = await fetch(`${API_BASE}/api/market-data/latest`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const json = (await res.json()) as { data: MarketQuote[] };
  return json.data;
}

export async function fetchPriceHistory(
  symbol: string,
  days = 30,
): Promise<MarketDataHistoryResponse> {
  const res = await fetch(
    `${API_BASE}/api/market-data/history?symbol=${encodeURIComponent(symbol)}&days=${days}`,
  );
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<MarketDataHistoryResponse>;
}
