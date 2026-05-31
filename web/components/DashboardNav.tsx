import Link from "next/link";

const NAV = [
  { href: "/feed", label: "TERMINAL" },
  { href: "/desk", label: "DESK" },
  { href: "/models", label: "MODELS" },
  { href: "/watchlist", label: "WATCHLIST" },
  { href: "/settings", label: "SETTINGS" },
];

export function DashboardNav() {
  return (
    <nav className="border-b border-border bg-surface px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
      <Link href="/feed" className="font-mono text-accent terminal-glow text-sm tracking-widest">
        PRICING_SENTINEL
      </Link>
      <div className="flex gap-4 flex-wrap">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="font-mono text-xs text-muted hover:text-accent transition-colors tracking-wider"
          >
            {item.label}
          </Link>
        ))}
        <Link
          href="/pricing"
          className="font-mono text-xs text-background bg-accent px-2 py-0.5 hover:bg-accent-dim transition-colors tracking-wider"
        >
          UPGRADE
        </Link>
      </div>
    </nav>
  );
}
