"use client";

import { useState } from "react";
import { fmtPercent, fmtPrice } from "@/lib/format";
import type { PricePoint, PriceUpdate, WatchlistEntry } from "@/lib/types";
import { Panel } from "./Panel";
import { Sparkline } from "./Sparkline";

export function Watchlist({
  entries,
  prices,
  history,
  selected,
  onSelect,
  onAdd,
  onRemove,
}: {
  entries: WatchlistEntry[];
  prices: Record<string, PriceUpdate>;
  history: Record<string, PricePoint[]>;
  selected: string;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => Promise<void>;
  onRemove: (ticker: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");

  const submit = async () => {
    if (!draft.trim()) return;
    try {
      await onAdd(draft.trim());
      setDraft("");
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add");
    }
  };

  return (
    <Panel label="Watchlist" bootDelay={50}>
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1 overflow-y-auto">
          {entries.map((entry) => (
            <Row
              key={entry.ticker}
              ticker={entry.ticker}
              update={prices[entry.ticker] ?? entry.price}
              points={history[entry.ticker] ?? []}
              selected={entry.ticker === selected}
              onSelect={() => onSelect(entry.ticker)}
              onRemove={() => onRemove(entry.ticker)}
            />
          ))}
        </div>
        <div className="shrink-0 border-t border-edge p-2">
          <div className="flex gap-1">
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="ADD TICKER"
              maxLength={5}
              className="w-full min-w-0 border border-edge bg-panel-2 px-2 py-1 text-[12px] tracking-widest placeholder:text-muted/50 focus:border-blue focus:outline-none"
            />
            <button
              onClick={submit}
              className="shrink-0 border border-purple bg-purple/30 px-2.5 text-[11px] tracking-widest text-purple-bright hover:bg-purple/60 hover:text-white"
            >
              +
            </button>
          </div>
          {error && <p className="mt-1 text-[10px] text-down">{error}</p>}
        </div>
      </div>
    </Panel>
  );
}

function Row({
  ticker,
  update,
  points,
  selected,
  onSelect,
  onRemove,
}: {
  ticker: string;
  update: PriceUpdate | null;
  points: PricePoint[];
  selected: boolean;
  onSelect: () => void;
  onRemove: () => void;
}) {
  // Session change: vs the first price seen since page load
  const base = points[0]?.price;
  const sessionPct = update && base ? ((update.price - base) / base) * 100 : 0;
  const flash =
    update?.direction === "up" ? "flash-up" : update?.direction === "down" ? "flash-down" : "";

  return (
    <div
      onClick={onSelect}
      className={`group flex cursor-pointer items-center gap-2 border-b border-edge/60 px-3 py-1.5 hover:bg-panel-2 ${
        selected ? "border-l-2 border-l-accent bg-panel-2" : "border-l-2 border-l-transparent"
      }`}
    >
      <div className="w-14">
        <div className="text-[13px] font-semibold tracking-wider text-white">{ticker}</div>
        <div
          className={`text-[10px] tabular-nums ${sessionPct >= 0 ? "text-up" : "text-down"}`}
        >
          {update && base ? fmtPercent(sessionPct) : "--"}
        </div>
      </div>
      <Sparkline points={points} />
      <div className="ml-auto text-right">
        {update ? (
          <span
            key={update.timestamp}
            className={`block px-1 text-[13px] tabular-nums ${flash} ${
              update.direction === "up"
                ? "text-up"
                : update.direction === "down"
                  ? "text-down"
                  : "text-white"
            }`}
          >
            {fmtPrice(update.price)}
          </span>
        ) : (
          <span className="text-muted">--</span>
        )}
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        title={`Remove ${ticker}`}
        className="w-4 shrink-0 text-muted/0 hover:text-down group-hover:text-muted"
      >
        ×
      </button>
    </div>
  );
}
