"use client";

import {
  AreaSeries,
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Snapshot } from "@/lib/types";
import { Panel } from "./Panel";
import { Empty } from "./Heatmap";

export function PnlChart({ snapshots }: { snapshots: Snapshot[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8b96a5",
        fontFamily: "var(--font-jetbrains), monospace",
        fontSize: 10,
        attributionLogo: false,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: "rgba(30,39,52,0.6)" },
      },
      rightPriceScale: { borderColor: "#1e2734" },
      timeScale: { borderColor: "#1e2734", timeVisible: true },
    });
    const series = chart.addSeries(AreaSeries, {
      lineColor: "#ecad0a",
      lineWidth: 2,
      topColor: "rgba(236,173,10,0.30)",
      bottomColor: "rgba(236,173,10,0.02)",
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const observer = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    const seen = new Set<number>();
    const data = [];
    for (const s of snapshots) {
      const time = Math.floor(new Date(s.recorded_at).getTime() / 1000);
      if (seen.has(time)) continue;
      seen.add(time);
      data.push({ time: time as UTCTimestamp, value: s.total_value });
    }
    data.sort((a, b) => (a.time as number) - (b.time as number));
    series.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [snapshots]);

  return (
    <Panel label="P&L — Total Value" bootDelay={250}>
      <div className="relative h-full w-full">
        <div ref={containerRef} className="h-full w-full" />
        {snapshots.length === 0 && (
          <div className="absolute inset-0">
            <Empty text="AWAITING SNAPSHOTS" />
          </div>
        )}
      </div>
    </Panel>
  );
}
