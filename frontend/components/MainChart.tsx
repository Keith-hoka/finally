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
import { fmtPercent, fmtPrice } from "@/lib/format";
import type { PricePoint, PriceUpdate } from "@/lib/types";
import { Panel } from "./Panel";

const CHART_OPTIONS = {
  layout: {
    background: { type: ColorType.Solid, color: "transparent" },
    textColor: "#8b96a5",
    fontFamily: "var(--font-jetbrains), monospace",
    fontSize: 10,
    attributionLogo: false,
  },
  grid: {
    vertLines: { color: "rgba(30,39,52,0.6)" },
    horzLines: { color: "rgba(30,39,52,0.6)" },
  },
  rightPriceScale: { borderColor: "#1e2734" },
  timeScale: { borderColor: "#1e2734", timeVisible: true, secondsVisible: true },
  crosshair: {
    horzLine: { color: "#ecad0a", labelBackgroundColor: "#ecad0a" },
    vertLine: { color: "#ecad0a", labelBackgroundColor: "#ecad0a" },
  },
};

export function MainChart({
  ticker,
  update,
  points,
}: {
  ticker: string;
  update: PriceUpdate | null;
  points: PricePoint[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const tickerRef = useRef(ticker);
  const countRef = useRef(0);
  const interactedRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Auto-fit the view as data streams in, but stop once the user pans/zooms
    const markInteracted = () => {
      interactedRef.current = true;
    };
    container.addEventListener("mousedown", markInteracted);
    container.addEventListener("wheel", markInteracted);
    container.addEventListener("touchstart", markInteracted);

    const chart = createChart(container, CHART_OPTIONS);
    const series = chart.addSeries(AreaSeries, {
      lineColor: "#209dd7",
      lineWidth: 2,
      topColor: "rgba(32,157,215,0.35)",
      bottomColor: "rgba(32,157,215,0.02)",
      priceLineColor: "#ecad0a",
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const observer = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    observer.observe(container);

    return () => {
      container.removeEventListener("mousedown", markInteracted);
      container.removeEventListener("wheel", markInteracted);
      container.removeEventListener("touchstart", markInteracted);
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    const data = points.map((p) => ({ time: p.time as UTCTimestamp, value: p.price }));
    const tickerChanged = tickerRef.current !== ticker;
    if (tickerChanged || countRef.current === 0 || data.length < countRef.current) {
      tickerRef.current = ticker;
      series.setData(data);
      interactedRef.current = false;
    } else if (data.length > 0) {
      series.update(data[data.length - 1]);
    }
    countRef.current = data.length;
    if (!interactedRef.current) chartRef.current?.timeScale().fitContent();
  }, [ticker, points, update]);

  return (
    <Panel
      label={`Chart — ${ticker}`}
      className="flex-1"
      bootDelay={100}
      right={
        update && (
          <span className="flex items-baseline gap-2 tabular-nums">
            <span className="text-[13px] font-semibold text-white">{fmtPrice(update.price)}</span>
            <span
              className={`text-[11px] ${update.direction === "down" ? "text-down" : "text-up"}`}
            >
              {fmtPercent(update.change_percent)}
            </span>
          </span>
        )
      }
    >
      <div ref={containerRef} className="h-full w-full" />
    </Panel>
  );
}
