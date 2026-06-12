"use client";

import { fmtPercent } from "@/lib/format";
import type { Position } from "@/lib/types";
import { Panel } from "./Panel";

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
  position: Position;
}

/** Binary-split treemap: weight by market value, color by P&L. */
function layout(items: Position[], x: number, y: number, w: number, h: number, out: Rect[]) {
  if (items.length === 0) return;
  if (items.length === 1) {
    out.push({ x, y, w, h, position: items[0] });
    return;
  }
  const total = items.reduce((sum, p) => sum + p.market_value, 0);
  let acc = 0;
  let split = 1;
  for (; split < items.length; split++) {
    acc += items[split - 1].market_value;
    if (acc >= total / 2) break;
  }
  const fraction = total > 0 ? acc / total : 0.5;
  const head = items.slice(0, split);
  const tail = items.slice(split);
  if (w >= h) {
    layout(head, x, y, w * fraction, h, out);
    layout(tail, x + w * fraction, y, w * (1 - fraction), h, out);
  } else {
    layout(head, x, y, w, h * fraction, out);
    layout(tail, x, y + h * fraction, w, h * (1 - fraction), out);
  }
}

function cellColor(pnlPercent: number): string {
  const intensity = Math.min(Math.abs(pnlPercent) / 5, 1);
  return pnlPercent >= 0
    ? `rgba(47, 191, 113, ${0.12 + intensity * 0.55})`
    : `rgba(229, 72, 77, ${0.12 + intensity * 0.55})`;
}

export function Heatmap({
  positions,
  onSelect,
}: {
  positions: Position[];
  onSelect: (ticker: string) => void;
}) {
  const sorted = [...positions].sort((a, b) => b.market_value - a.market_value);
  const rects: Rect[] = [];
  layout(sorted, 0, 0, 100, 100, rects);

  return (
    <Panel label="Portfolio Heatmap" bootDelay={200}>
      {rects.length === 0 ? (
        <Empty text="NO POSITIONS" />
      ) : (
        <div className="relative h-full w-full">
          {rects.map(({ x, y, w, h, position }) => (
            <button
              key={position.ticker}
              onClick={() => onSelect(position.ticker)}
              className="absolute overflow-hidden border border-bg text-left transition-colors hover:brightness-125"
              style={{
                left: `${x}%`,
                top: `${y}%`,
                width: `${w}%`,
                height: `${h}%`,
                backgroundColor: cellColor(position.pnl_percent),
              }}
              title={`${position.ticker}: ${fmtPercent(position.pnl_percent)}`}
            >
              <div className="p-1.5">
                <div className="text-[11px] font-bold tracking-wider text-white">
                  {position.ticker}
                </div>
                <div
                  className={`text-[10px] tabular-nums ${
                    position.pnl_percent >= 0 ? "text-up" : "text-down"
                  }`}
                >
                  {fmtPercent(position.pnl_percent)}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </Panel>
  );
}

export function Empty({ text }: { text: string }) {
  return (
    <div className="flex h-full items-center justify-center">
      <span className="panel-label opacity-60">{text}</span>
    </div>
  );
}
