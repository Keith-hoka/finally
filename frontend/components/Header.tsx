"use client";

import { fmtMoney } from "@/lib/format";
import type { ConnectionStatus } from "@/lib/types";

const STATUS_STYLE: Record<ConnectionStatus, { color: string; pulse: boolean; label: string }> = {
  connected: { color: "#2fbf71", pulse: false, label: "LIVE" },
  reconnecting: { color: "#ecad0a", pulse: true, label: "RECONNECTING" },
  disconnected: { color: "#e5484d", pulse: false, label: "OFFLINE" },
};

export function Header({
  totalValue,
  cash,
  status,
}: {
  totalValue: number;
  cash: number;
  status: ConnectionStatus;
}) {
  const s = STATUS_STYLE[status];
  return (
    <header className="flex h-12 shrink-0 items-center gap-6 border-b border-edge bg-panel px-4">
      <h1
        className="text-[15px] tracking-[0.3em] text-accent"
        style={{ fontFamily: "var(--font-display)" }}
      >
        FIN<span className="text-blue">ALLY</span>
      </h1>
      <span className="hidden text-[10px] tracking-[0.18em] text-muted lg:block">
        AI TRADING WORKSTATION
      </span>

      <div className="ml-auto flex items-center gap-6">
        <Stat label="PORTFOLIO" value={fmtMoney(totalValue)} valueClass="text-accent" />
        <Stat label="CASH" value={fmtMoney(cash)} valueClass="text-blue" />
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${s.pulse ? "pulse-dot" : ""}`}
            style={{ backgroundColor: s.color }}
            title={`Stream: ${status}`}
          />
          <span className="text-[10px] tracking-[0.15em] text-muted">{s.label}</span>
        </div>
      </div>
    </header>
  );
}

function Stat({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass: string;
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="panel-label">{label}</span>
      <span className={`text-[15px] font-semibold tabular-nums ${valueClass}`}>{value}</span>
    </div>
  );
}
