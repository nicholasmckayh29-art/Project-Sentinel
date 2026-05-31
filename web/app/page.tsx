"use client";

import { TerminalPreview } from "@/components/terminal/TerminalPreview";
import Link from "next/link";
import { useEffect, useState } from "react";
import { TerminalBoot } from "@/components/TerminalBoot";

export default function LandingPage() {
  const [bootDone, setBootDone] = useState(false);
  const [skipBoot, setSkipBoot] = useState(false);

  useEffect(() => {
    if (document.cookie.includes("ps_session=1")) {
      setSkipBoot(true);
      setBootDone(true);
    }
  }, []);

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-6 py-16 max-w-3xl mx-auto">
      {!skipBoot && (
        <div className="w-full min-h-[120px] mb-8">
          <TerminalBoot onComplete={() => setBootDone(true)} />
        </div>
      )}

      {bootDone && (
        <div className="w-full space-y-8 animate-in fade-in duration-700">
          <div>
            <p className="badge-classified inline-block mb-4">CLEARANCE: PUBLIC</p>
            <h1 className="font-mono text-3xl md:text-4xl text-accent terminal-glow tracking-tight">
              AI MODEL INTELLIGENCE
            </h1>
            <p className="mt-4 text-muted text-lg leading-relaxed">
              Not another pricing dashboard. Insider signals on which model to use,
              when to switch, and why — before the market catches on.
            </p>
          </div>

          <TerminalPreview />

          <ul className="font-mono text-sm space-y-2 text-foreground/90">
            <li><span className="text-accent">▸</span> Terminal feed with live news wire and equity strip</li>
            <li><span className="text-accent">▸</span> Desk command center with multi-chart analytics</li>
            <li><span className="text-accent">▸</span> True Cost analysis, not raw token prices</li>
            <li><span className="text-accent">▸</span> Derived sentiment from HN, RSS, and research feeds</li>
          </ul>

          <div className="flex gap-4 flex-wrap">
            <Link
              href="/login"
              className="font-mono text-sm bg-accent text-background px-6 py-3 hover:bg-accent-dim transition-colors tracking-wider"
            >
              REQUEST ACCESS
            </Link>
            <Link
              href="/pricing"
              className="font-mono text-sm border border-border px-6 py-3 hover:border-accent hover:text-accent transition-colors tracking-wider"
            >
              VIEW CLEARANCE LEVELS
            </Link>
          </div>
        </div>
      )}
    </main>
  );
}
