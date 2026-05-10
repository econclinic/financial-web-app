"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/shared/navbar";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { useAuth } from "@/hooks/use-auth";
import { useLocale } from "@/hooks/use-locale";
import { createTransaction } from "@/lib/portfolio";

const SYMBOLS = ["BTC", "ETH", "AAPL"];

export default function NewTransactionPage() {
  const { token } = useAuth();
  const { t } = useLocale();
  const router = useRouter();

  const [symbol, setSymbol] = useState("BTC");
  const [assetType, setAssetType] = useState<"crypto" | "stock">("crypto");
  const [transactionType, setTransactionType] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSymbolChange(value: string) {
    setSymbol(value);
    setAssetType(value === "AAPL" ? "stock" : "crypto");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const qty = parseFloat(quantity);
    const prc = parseFloat(price);

    if (isNaN(qty) || qty <= 0) {
      setError("Quantity must be greater than 0");
      return;
    }
    if (isNaN(prc) || prc <= 0) {
      setError("Price must be greater than 0");
      return;
    }
    if (!token) return;

    setSubmitting(true);
    try {
      await createTransaction(token, {
        symbol,
        asset_type: assetType,
        transaction_type: transactionType,
        quantity: qty,
        price: prc,
      });
      router.push("/portfolio");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Transaction failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto max-w-lg px-4 py-6 sm:px-6 sm:py-8">
          <Link
            href="/portfolio"
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4 ltr:mr-1 rtl:ml-1 rtl:rotate-180" />
            {t("newTransaction.back")}
          </Link>

          <h2 className="mt-4 text-2xl font-bold tracking-tight">
            {t("newTransaction.title")}
          </h2>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div>
              <label
                htmlFor="symbol"
                className="mb-1.5 block text-sm font-medium"
              >
                {t("newTransaction.symbol")}
              </label>
              <select
                id="symbol"
                value={symbol}
                onChange={(e) => handleSymbolChange(e.target.value)}
                className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              >
                {SYMBOLS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium">
                {t("newTransaction.assetType")}
              </label>
              <div className="flex gap-3">
                {(["crypto", "stock"] as const).map((type) => (
                  <label
                    key={type}
                    className="flex items-center gap-2 text-sm"
                  >
                    <input
                      type="radio"
                      name="asset_type"
                      value={type}
                      checked={assetType === type}
                      onChange={() => setAssetType(type)}
                      className="accent-primary"
                    />
                    {t(`newTransaction.${type}`)}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium">
                {t("newTransaction.transactionType")}
              </label>
              <div className="flex gap-3">
                {(["buy", "sell"] as const).map((type) => (
                  <label
                    key={type}
                    className="flex items-center gap-2 text-sm"
                  >
                    <input
                      type="radio"
                      name="transaction_type"
                      value={type}
                      checked={transactionType === type}
                      onChange={() => setTransactionType(type)}
                      className="accent-primary"
                    />
                    {t(`newTransaction.${type}`)}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label
                htmlFor="quantity"
                className="mb-1.5 block text-sm font-medium"
              >
                {t("newTransaction.quantity")}
              </label>
              <input
                id="quantity"
                type="number"
                step="any"
                min="0"
                placeholder="0.00"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
                className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              />
            </div>

            <div>
              <label
                htmlFor="price"
                className="mb-1.5 block text-sm font-medium"
              >
                {t("newTransaction.price")}
              </label>
              <input
                id="price"
                type="number"
                step="any"
                min="0"
                placeholder="0.00"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
                className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              />
            </div>

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? t("newTransaction.submitting") : t("newTransaction.submit")}
            </Button>
          </form>
        </div>
      </main>
    </ProtectedRoute>
  );
}
