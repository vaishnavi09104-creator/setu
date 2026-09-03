"use client";

import { useState } from "react";
import type { ParsedMandate } from "@/lib/types";
import { parseMandate } from "@/lib/api";
import { FIXTURE_PRESETS } from "@/lib/fixtures";
import { Send, MessageSquareText, Loader2 } from "lucide-react";
import clsx from "clsx";

interface Msg {
  role: "user" | "system";
  text: string;
}

export function MandateChat({
  onParsed,
  onParsing,
}: {
  onParsed: (m: ParsedMandate) => void;
  onParsing?: (b: boolean) => void;
}) {
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "system", text: "Describe your CSR mandate in one sentence — budget, domains, districts. I'll structure it and ask if anything is unclear." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(text: string) {
    if (!text.trim() || busy) return;
    setMsgs((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);
    onParsing?.(true);
    try {
      const res = await parseMandate(text);
      onParsed(res.data);
      const n = res.data.clarifying_questions.length;
      setMsgs((m) => [
        ...m,
        {
          role: "system",
          text:
            n > 0
              ? `Structured on the right. ${n} clarification${n > 1 ? "s" : ""} needed — answer in one tap.`
              : "Structured on the right — every field extracted with confidence.",
        },
      ]);
    } finally {
      setBusy(false);
      onParsing?.(false);
    }
  }

  return (
    <div className="flex h-[560px] flex-col rounded-xl border border-line bg-surface">
      <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
        {msgs.map((m, i) => (
          <div key={i} className={clsx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={clsx(
                "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                m.role === "user" ? "rounded-br-sm bg-accent text-white" : "rounded-bl-sm border border-line bg-card text-ink",
              )}
            >
              {m.text}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm border border-line bg-card px-4 py-2.5 text-sm text-muted">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              parsing mandate…
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-line p-3">
        <div className="mb-2 flex flex-wrap gap-1.5">
          {FIXTURE_PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => submit(p.text)}
              className="rounded-full border border-line bg-card px-3 py-1 text-xs font-medium text-muted transition-colors duration-150 hover:border-accent hover:text-accent"
            >
              {p.label}
            </button>
          ))}
        </div>
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void submit(input);
          }}
        >
          <label htmlFor="mandate-input" className="sr-only">
            Describe your CSR mandate
          </label>
          <div className="relative flex-1">
            <MessageSquareText className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              id="mandate-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="₹50 lakh for maternal health and clean water across Kalahandi, Nuapada…"
              className="w-full rounded-lg border border-line bg-surface py-2.5 pl-9 pr-3 text-sm text-ink placeholder:text-slate-400"
              disabled={busy}
            />
          </div>
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="inline-flex h-10 items-center gap-1.5 rounded-lg bg-accent px-4 text-sm font-medium text-white transition-opacity duration-150 hover:opacity-90 disabled:opacity-40"
            aria-label="Parse mandate"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
            Parse
          </button>
        </form>
      </div>
    </div>
  );
}
