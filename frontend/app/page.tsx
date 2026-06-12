"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Chat } from "@/components/Chat";
import { Header } from "@/components/Header";
import { Heatmap } from "@/components/Heatmap";
import { MainChart } from "@/components/MainChart";
import { PnlChart } from "@/components/PnlChart";
import { PositionsTable } from "@/components/PositionsTable";
import { TradeBar } from "@/components/TradeBar";
import { Watchlist } from "@/components/Watchlist";
import {
  addToWatchlist,
  getHistory,
  getPortfolio,
  getWatchlist,
  removeFromWatchlist,
} from "@/lib/api";
import { usePrices } from "@/lib/usePrices";
import type { Portfolio, Snapshot, WatchlistEntry } from "@/lib/types";

const REFRESH_MS = 15_000;

export default function Workstation() {
  const { prices, status, history } = usePrices();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistEntry[]>([]);
  const [selected, setSelected] = useState("AAPL");

  const refresh = useCallback(() => {
    getPortfolio().then(setPortfolio).catch(() => {});
    getHistory().then(setSnapshots).catch(() => {});
    getWatchlist().then(setWatchlist).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  // Live total: cash plus positions marked to the streaming prices
  const liveTotal = useMemo(() => {
    if (!portfolio) return 0;
    return portfolio.positions.reduce(
      (sum, p) => sum + p.quantity * (prices[p.ticker]?.price ?? p.current_price),
      portfolio.cash_balance,
    );
  }, [portfolio, prices]);

  const handleAdd = async (ticker: string) => {
    await addToWatchlist(ticker);
    refresh();
  };

  const handleRemove = async (ticker: string) => {
    await removeFromWatchlist(ticker).catch(() => {});
    refresh();
  };

  return (
    <div className="flex h-full flex-col">
      <Header totalValue={liveTotal} cash={portfolio?.cash_balance ?? 0} status={status} />
      <div className="grid min-h-0 flex-1 grid-cols-[290px_1fr_350px] gap-px bg-edge">
        <Watchlist
          entries={watchlist}
          prices={prices}
          history={history}
          selected={selected}
          onSelect={setSelected}
          onAdd={handleAdd}
          onRemove={handleRemove}
        />

        <div className="grid min-h-0 grid-rows-[minmax(0,5fr)_minmax(0,4fr)] gap-px bg-edge">
          <div className="flex min-h-0 flex-col bg-panel">
            <MainChart
              ticker={selected}
              update={prices[selected] ?? null}
              points={history[selected] ?? []}
            />
            <TradeBar selected={selected} onExecuted={refresh} />
          </div>
          <div className="grid min-h-0 grid-cols-3 gap-px">
            <Heatmap positions={portfolio?.positions ?? []} onSelect={setSelected} />
            <PnlChart snapshots={snapshots} />
            <PositionsTable
              positions={portfolio?.positions ?? []}
              prices={prices}
              selected={selected}
              onSelect={setSelected}
            />
          </div>
        </div>

        <Chat onActions={refresh} />
      </div>
    </div>
  );
}
