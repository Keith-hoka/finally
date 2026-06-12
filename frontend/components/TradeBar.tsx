"use client";

import { useState } from "react";
import { executeTrade } from "@/lib/api";
import { fmtMoney } from "@/lib/format";
import type { TradeResult } from "@/lib/types";

export function TradeBar({
  selected,
  onExecuted,
}: {
  selected: string;
  onExecuted: () => void;
}) {
  const [ticker, setTicker] = useState(selected);
  const [quantity, setQuantity] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ text: string; error: boolean } | null>(null);

  // Follow the selected ticker (adjust-during-render, per React docs)
  const [lastSelected, setLastSelected] = useState(selected);
  if (selected !== lastSelected) {
    setLastSelected(selected);
    setTicker(selected);
  }

  const submit = async (side: "buy" | "sell") => {
    const qty = parseFloat(quantity);
    if (!ticker.trim() || !qty || qty <= 0) {
      setNotice({ text: "Enter a ticker and a positive quantity", error: true });
      return;
    }
    setBusy(true);
    try {
      const result: TradeResult = await executeTrade(ticker.trim(), qty, side);
      setNotice({
        text: `${side.toUpperCase()} ${result.quantity} ${result.ticker} @ ${fmtMoney(result.price)} — cash ${fmtMoney(result.cash_balance)}`,
        error: false,
      });
      setQuantity("");
      onExecuted();
    } catch (e) {
      setNotice({ text: e instanceof Error ? e.message : "Trade failed", error: true });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="boot-in flex shrink-0 items-center gap-2 border-t border-edge bg-panel px-3 py-2" style={{ animationDelay: "150ms" }}>
      <span className="panel-label">Trade</span>
      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
        maxLength={5}
        className="w-20 border border-edge bg-panel-2 px-2 py-1 text-[12px] tracking-widest focus:border-blue focus:outline-none"
        aria-label="Ticker"
      />
      <input
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit("buy")}
        placeholder="QTY"
        inputMode="decimal"
        className="w-24 border border-edge bg-panel-2 px-2 py-1 text-[12px] tabular-nums placeholder:text-muted/50 focus:border-blue focus:outline-none"
        aria-label="Quantity"
      />
      <button
        onClick={() => submit("buy")}
        disabled={busy}
        className="border border-purple bg-purple/40 px-4 py-1 text-[11px] font-semibold tracking-[0.2em] text-up hover:bg-purple/70 disabled:opacity-40"
      >
        BUY
      </button>
      <button
        onClick={() => submit("sell")}
        disabled={busy}
        className="border border-purple bg-purple/40 px-4 py-1 text-[11px] font-semibold tracking-[0.2em] text-down hover:bg-purple/70 disabled:opacity-40"
      >
        SELL
      </button>
      {notice && (
        <span className={`truncate text-[11px] ${notice.error ? "text-down" : "text-muted"}`}>
          {notice.text}
        </span>
      )}
    </div>
  );
}
