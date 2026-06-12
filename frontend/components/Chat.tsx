"use client";

import { useEffect, useRef, useState } from "react";
import { getChatHistory, sendChat } from "@/lib/api";
import { fmtMoney } from "@/lib/format";
import type { ChatActions, ChatMessage } from "@/lib/types";
import { Panel } from "./Panel";

export function Chat({ onActions }: { onActions: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getChatHistory().then(setMessages).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, busy]);

  const submit = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    setMessages((m) => [...m, { role: "user", content: text, actions: null }]);
    setBusy(true);
    try {
      const reply = await sendChat(text);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: reply.message, actions: reply.actions },
      ]);
      const acted =
        reply.actions.trades.length > 0 || reply.actions.watchlist_changes.length > 0;
      if (acted) onActions();
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: e instanceof Error ? e.message : "Something went wrong.",
          actions: null,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel label="FinAlly AI" bootDelay={350}>
      <div className="flex h-full flex-col">
        <div ref={scrollRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
          {messages.length === 0 && !busy && (
            <p className="text-[11px] leading-relaxed text-muted">
              Ask me about your portfolio, market moves, or tell me to trade for you.
              <br />
              <br />
              <span className="text-blue">&gt;</span> “What’s my biggest risk?”
              <br />
              <span className="text-blue">&gt;</span> “Buy $500 of NVDA”
            </p>
          )}
          {messages.map((message, i) => (
            <Bubble key={i} message={message} />
          ))}
          {busy && (
            <div className="text-[12px] text-blue">
              FINALLY<span className="blink-cursor">▋</span>
            </div>
          )}
        </div>
        <div className="shrink-0 border-t border-edge p-2">
          <div className="flex gap-1">
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Message FinAlly…"
              disabled={busy}
              className="w-full min-w-0 border border-edge bg-panel-2 px-2 py-1.5 text-[12px] placeholder:text-muted/50 focus:border-blue focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={submit}
              disabled={busy || !draft.trim()}
              className="shrink-0 border border-purple bg-purple/40 px-3 text-[11px] tracking-[0.2em] text-white hover:bg-purple/70 disabled:opacity-40"
            >
              SEND
            </button>
          </div>
        </div>
      </div>
    </Panel>
  );
}

function Bubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={isUser ? "pl-6" : "pr-2"}>
      <div className={`text-[9px] tracking-[0.2em] ${isUser ? "text-right text-muted" : "text-blue"}`}>
        {isUser ? "YOU" : "FINALLY"}
      </div>
      <div
        className={`mt-0.5 whitespace-pre-wrap border px-2.5 py-1.5 text-[12px] leading-relaxed ${
          isUser
            ? "border-edge bg-panel-2 text-white"
            : "border-blue/25 bg-blue/5 text-[#d7dee8]"
        }`}
      >
        {message.content}
      </div>
      {message.actions && <ActionReceipts actions={message.actions} />}
    </div>
  );
}

function ActionReceipts({ actions }: { actions: ChatActions }) {
  if (!actions.trades.length && !actions.watchlist_changes.length && !actions.errors.length)
    return null;
  return (
    <div className="mt-1 space-y-0.5">
      {actions.trades.map((t, i) => (
        <div key={`t${i}`} className="border-l-2 border-accent bg-accent/5 px-2 py-1 text-[10px] tracking-wide text-accent">
          EXECUTED: {t.side.toUpperCase()} {t.quantity} {t.ticker} @ {fmtMoney(t.price)}
        </div>
      ))}
      {actions.watchlist_changes.map((c, i) => (
        <div key={`w${i}`} className="border-l-2 border-blue bg-blue/5 px-2 py-1 text-[10px] tracking-wide text-blue">
          WATCHLIST: {c.action.toUpperCase()} {c.ticker}
        </div>
      ))}
      {actions.errors.map((err, i) => (
        <div key={`e${i}`} className="border-l-2 border-down bg-down/5 px-2 py-1 text-[10px] tracking-wide text-down">
          REJECTED: {err}
        </div>
      ))}
    </div>
  );
}
