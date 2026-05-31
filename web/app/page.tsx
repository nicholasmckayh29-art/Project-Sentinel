"use client";

import Link from "next/link";
import { useState } from "react";
import { TerminalBoot } from "@/components/TerminalBoot";

export default function LandingPage() {
  const [bootDone, setBootDone] = useState(false);

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-6 py-16 max-w-3xl mx-auto">
      <div className="w-full min-h-[120px] mb-8">
        <TerminalBoot onComplete={() => setBootDone(true)} />
      </div>

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

          <ul className="font-mono text-sm space-y-2 text-foreground/90">
            <li><span className="text-accent">▸</span> Track providers, models, and workloads</li>
            <li><span className="text-accent">▸</span> Real-time drop and spike alerts</li>
            <li><span className="text-accent">▸</span> True Cost analysis, not raw token prices</li>
            <li><span className="text-accent">▸</span> AI news and release radar</li>
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
