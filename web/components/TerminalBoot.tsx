"use client";

import { useEffect, useState } from "react";

const LINES = [
  "> INITIALIZING SENTINEL...",
  "> CONNECTING TO PRICE FEEDS...",
  "> LOADING TRUE COST ENGINE...",
  "> ACCESS GRANTED.",
];

export function TerminalBoot({ onComplete }: { onComplete?: () => void }) {
  const [lineIndex, setLineIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (lineIndex >= LINES.length) {
      setDone(true);
      onComplete?.();
      return;
    }
    const line = LINES[lineIndex];
    if (charIndex < line.length) {
      const t = setTimeout(() => setCharIndex((c) => c + 1), 18);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      setLineIndex((i) => i + 1);
      setCharIndex(0);
    }, 400);
    return () => clearTimeout(t);
  }, [lineIndex, charIndex, onComplete]);

  if (done) return null;

  return (
    <div className="font-mono text-sm text-accent terminal-glow space-y-1">
      {LINES.slice(0, lineIndex).map((line) => (
        <div key={line}>{line}</div>
      ))}
      {lineIndex < LINES.length && (
        <div className="cursor-blink">
          {LINES[lineIndex].slice(0, charIndex)}
        </div>
      )}
    </div>
  );
}
