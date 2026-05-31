"use client";

/** Static terminal preview for landing — no live data required. */
export function TerminalPreview() {
  const demoTicks = [
    { label: "GPT-4o", val: "$2.50/1M", ch: "-12.0%" },
    { label: "Claude", val: "$3.00/1M", ch: "+2.1%" },
    { label: "NVDA", val: "$875.28", ch: "+1.4%" },
    { label: "MSFT", val: "$415.50", ch: "-0.3%" },
  ];

  return (
    <div className="border border-border bg-surface overflow-hidden font-mono text-xs">
      <div className="px-3 py-2 border-b border-border text-accent tracking-widest">
        TERMINAL PREVIEW
      </div>
      <div className="flex gap-6 px-4 py-2 border-b border-border overflow-x-auto">
        {demoTicks.map((t) => (
          <span key={t.label} className="whitespace-nowrap">
            <span className="text-accent">{t.label}</span> {t.val}{" "}
            <span className={t.ch.startsWith("-") ? "text-alert-drop" : "text-alert-increase"}>
              {t.ch}
            </span>
          </span>
        ))}
      </div>
      <div className="grid sm:grid-cols-2 divide-x divide-border">
        <div className="p-3 space-y-1">
          <p className="text-muted text-[10px] tracking-widest">PRICE TAPE</p>
          <p><span className="text-alert-drop">▼</span> gpt-4o-mini · -15.2%</p>
          <p><span className="text-alert-increase">▲</span> claude-3-haiku · +3.1%</p>
        </div>
        <div className="p-3 space-y-1">
          <p className="text-muted text-[10px] tracking-widest">NEWS WIRE</p>
          <p className="line-clamp-1">Open-source LLM benchmark shifts routing economics</p>
          <p className="line-clamp-1 text-muted">HN · 142 pts · 2h ago</p>
        </div>
      </div>
      <div className="px-3 py-2 border-t border-border text-muted text-[10px]">
        SENTIMENT · DERIVED · 62 BULLISH
      </div>
    </div>
  );
}
