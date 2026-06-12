"use client";

import { fmtMoney, fmtPercent, fmtPrice, fmtQuantity, pnlColor } from "@/lib/format";
import type { Position, PriceUpdate } from "@/lib/types";
import { Panel } from "./Panel";
import { Empty } from "./Heatmap";

export function PositionsTable({
  positions,
  prices,
  selected,
  onSelect,
}: {
  positions: Position[];
  prices: Record<string, PriceUpdate>;
  selected: string;
  onSelect: (ticker: string) => void;
}) {
  return (
    <Panel label="Positions" bootDelay={300}>
      {positions.length === 0 ? (
        <Empty text="NO OPEN POSITIONS" />
      ) : (
        <div className="h-full overflow-y-auto">
          <table className="w-full text-right tabular-nums">
            <thead className="sticky top-0 bg-panel">
              <tr className="border-b border-edge text-[10px] tracking-[0.15em] text-muted">
                <th className="px-3 py-1.5 text-left font-normal">TICKER</th>
                <th className="px-3 py-1.5 font-normal">QTY</th>
                <th className="px-3 py-1.5 font-normal">AVG COST</th>
                <th className="px-3 py-1.5 font-normal">LAST</th>
                <th className="px-3 py-1.5 font-normal">VALUE</th>
                <th className="px-3 py-1.5 font-normal">P&L</th>
                <th className="px-3 py-1.5 font-normal">%</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => {
                const live = prices[p.ticker]?.price ?? p.current_price;
                const value = p.quantity * live;
                const pnl = value - p.quantity * p.avg_cost;
                const pct = p.avg_cost ? (pnl / (p.quantity * p.avg_cost)) * 100 : 0;
                return (
                  <tr
                    key={p.ticker}
                    onClick={() => onSelect(p.ticker)}
                    className={`cursor-pointer border-b border-edge/50 text-[12px] hover:bg-panel-2 ${
                      p.ticker === selected ? "bg-panel-2" : ""
                    }`}
                  >
                    <td className="px-3 py-1.5 text-left font-semibold tracking-wider text-white">
                      {p.ticker}
                    </td>
                    <td className="px-3 py-1.5">{fmtQuantity(p.quantity)}</td>
                    <td className="px-3 py-1.5">{fmtPrice(p.avg_cost)}</td>
                    <td className="px-3 py-1.5">{fmtPrice(live)}</td>
                    <td className="px-3 py-1.5">{fmtMoney(value)}</td>
                    <td className={`px-3 py-1.5 ${pnlColor(pnl)}`}>{fmtMoney(pnl)}</td>
                    <td className={`px-3 py-1.5 ${pnlColor(pnl)}`}>{fmtPercent(pct)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
