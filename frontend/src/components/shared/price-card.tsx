import { TrendingDown, TrendingUp } from "lucide-react";

interface PriceCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  selected?: boolean;
  onClick?: () => void;
}

export function PriceCard({
  symbol,
  name,
  price,
  change,
  changePercent,
  selected,
  onClick,
}: PriceCardProps) {
  const isPositive = change >= 0;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-xl border bg-card p-5 text-left shadow-sm transition-colors hover:bg-accent/50 ${
        selected ? "ring-2 ring-primary" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{name}</p>
          <p className="text-xs text-muted-foreground">{symbol}</p>
        </div>
        {isPositive ? (
          <TrendingUp className="h-5 w-5 text-green-500" />
        ) : (
          <TrendingDown className="h-5 w-5 text-red-500" />
        )}
      </div>
      <p className="mt-3 text-2xl font-semibold">
        ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </p>
      <p
        className={`mt-1 text-sm font-medium ${isPositive ? "text-green-500" : "text-red-500"}`}
      >
        {isPositive ? "+" : ""}
        {change.toFixed(2)} ({isPositive ? "+" : ""}
        {changePercent.toFixed(2)}%)
      </p>
    </button>
  );
}
