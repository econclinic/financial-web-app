/**
 * Mock benchmark data for BTC and S&P 500.
 * Uses deterministic seed-based generation so charts are stable across renders.
 */

export type BenchmarkId = "none" | "btc" | "sp500";

export interface BenchmarkPoint {
  timestamp: string;
  value: number;
}

const RANGE_DAYS: Record<string, number> = {
  "1m": 30,
  "3m": 90,
  "6m": 180,
  "1y": 365,
  all: 730,
};

/** Simple seeded pseudo-random number generator (mulberry32). */
function seededRandom(seed: number): () => number {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function generateSeries(
  basePriceStart: number,
  dailyDriftPct: number,
  dailyVolPct: number,
  days: number,
  seed: number,
): BenchmarkPoint[] {
  const rng = seededRandom(seed);
  const points: BenchmarkPoint[] = [];
  let price = basePriceStart;
  const now = Date.now();

  for (let i = days; i >= 0; i--) {
    const ts = new Date(now - i * 86400000).toISOString();
    points.push({ timestamp: ts, value: Math.round(price * 100) / 100 });
    const shock = (rng() - 0.5) * 2 * dailyVolPct;
    price *= 1 + dailyDriftPct + shock;
  }

  return points;
}

export function getBenchmarkData(
  benchmarkId: BenchmarkId,
  range: string,
): BenchmarkPoint[] {
  if (benchmarkId === "none") return [];

  const days = RANGE_DAYS[range] ?? 30;

  if (benchmarkId === "btc") {
    return generateSeries(62000, 0.001, 0.03, days, 42);
  }

  // S&P 500
  return generateSeries(5200, 0.0003, 0.008, days, 99);
}

export function getBenchmarkLabel(benchmarkId: BenchmarkId): string {
  switch (benchmarkId) {
    case "btc":
      return "BTC";
    case "sp500":
      return "S&P 500";
    default:
      return "";
  }
}
