import type { ReactNode } from "react";

export function Panel({
  label,
  right,
  children,
  className = "",
  bootDelay = 0,
}: {
  label: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  bootDelay?: number;
}) {
  return (
    <section
      className={`boot-in flex min-h-0 flex-col bg-panel ${className}`}
      style={{ animationDelay: `${bootDelay}ms` }}
    >
      <header className="flex h-7 shrink-0 items-center justify-between border-b border-edge px-3">
        <h2 className="panel-label">{label}</h2>
        {right}
      </header>
      <div className="min-h-0 flex-1">{children}</div>
    </section>
  );
}
