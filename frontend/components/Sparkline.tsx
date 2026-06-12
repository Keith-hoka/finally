"use client";

import { useEffect, useRef } from "react";
import type { PricePoint } from "@/lib/types";

/** Tiny canvas line chart of price action accumulated since page load. */
export function Sparkline({
  points,
  width = 72,
  height = 22,
}: {
  points: PricePoint[];
  width?: number;
  height?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);
    if (points.length < 2) return;

    const values = points.map((p) => p.price);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const up = values[values.length - 1] >= values[0];
    const color = up ? "#2fbf71" : "#e5484d";

    ctx.beginPath();
    points.forEach((p, i) => {
      const x = (i / (points.length - 1)) * (width - 2) + 1;
      const y = height - 2 - ((p.price - min) / span) * (height - 4);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.lineTo(width - 1, height);
    ctx.lineTo(1, height);
    ctx.closePath();
    const fill = ctx.createLinearGradient(0, 0, 0, height);
    fill.addColorStop(0, up ? "rgba(47,191,113,0.25)" : "rgba(229,72,77,0.25)");
    fill.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = fill;
    ctx.fill();
  }, [points, width, height]);

  return <canvas ref={canvasRef} style={{ width, height }} />;
}
