const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface PortfolioTransaction {
  id: number;
  user_id: number;
  symbol: string;
  asset_type: "crypto" | "stock";
  transaction_type: "buy" | "sell";
  quantity: number;
  price: number;
  timestamp: string;
}

export interface PortfolioPosition {
  symbol: string;
  asset_type: "crypto" | "stock";
  total_quantity: number;
  average_buy_price: number;
  current_price: number;
  total_value: number;
  unrealized_pnl: number;
}

export interface PortfolioSummary {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  pnl_percentage: number;
  positions: PortfolioPosition[];
}

export interface TransactionCreatePayload {
  symbol: string;
  asset_type: "crypto" | "stock";
  transaction_type: "buy" | "sell";
  quantity: number;
  price: number;
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function fetchPortfolioSummary(
  token: string,
): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE}/api/portfolio/summary`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<PortfolioSummary>;
}

export async function fetchTransactions(
  token: string,
): Promise<PortfolioTransaction[]> {
  const res = await fetch(`${API_BASE}/api/portfolio/transactions`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<PortfolioTransaction[]>;
}

export interface MarketPriceInfo {
  price: number;
  change_24h: number;
}

export async function fetchMarketPrices(
  token: string,
  symbols: string[] = ["BTC", "ETH"],
): Promise<Record<string, MarketPriceInfo>> {
  const res = await fetch(
    `${API_BASE}/api/market/prices?symbols=${symbols.join(",")}`,
    { headers: authHeaders(token) },
  );
  if (!res.ok) throw new Error(`Market data unavailable (${res.status})`);
  return res.json() as Promise<Record<string, MarketPriceInfo>>;
}

export async function createTransaction(
  token: string,
  data: TransactionCreatePayload,
): Promise<PortfolioTransaction> {
  const res = await fetch(`${API_BASE}/api/portfolio/transactions`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail ?? `Transaction failed (${res.status})`);
  }
  return res.json() as Promise<PortfolioTransaction>;
}
