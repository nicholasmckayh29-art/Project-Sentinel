"use client";

import type { MarketEvent } from "@/lib/market-types";

function NewsItem({ item, flash }: { item: MarketEvent; flash: boolean }) {
  const og = item.metadata?.og as { image?: string; description?: string } | undefined;

  return (
    <article
      className={`px-3 py-2 border-b border-border transition-colors ${
        flash ? "bg-surface-elevated" : ""
      }`}
    >
      <div className="flex gap-2 items-start">
        {og?.image && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={og.image} alt="" className="w-10 h-10 object-cover shrink-0 border border-border" />
        )}
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[10px] text-muted uppercase">
            {item.source ?? "—"} · {item.event_type}
          </p>
          {item.url ? (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs hover:text-accent line-clamp-2"
            >
              {item.title}
            </a>
          ) : (
            <p className="font-mono text-xs line-clamp-2">{item.title}</p>
          )}
          <p className="font-mono text-[10px] text-muted mt-0.5">
            {new Date(item.published_at).toLocaleString()}
          </p>
        </div>
      </div>
    </article>
  );
}

export function NewsWireLive({
  news,
  flashId,
}: {
  news: MarketEvent[];
  flashId: string | null;
}) {
  return (
    <div className="card-terminal h-full flex flex-col min-h-[280px]">
      <div className="px-3 py-2 border-b border-border">
        <h2 className="font-mono text-xs text-accent tracking-widest">NEWS WIRE</h2>
      </div>
      <div className="flex-1 overflow-y-auto max-h-[420px]">
        {news.length === 0 ? (
          <p className="font-mono text-xs text-muted p-3">&gt; NO INTEL ON FILE</p>
        ) : (
          news.map((item) => (
            <NewsItem key={item.id} item={item} flash={flashId === item.id} />
          ))
        )}
      </div>
    </div>
  );
}

export function ResearchWire({ events }: { events: MarketEvent[] }) {
  const research = events.filter((e) => e.event_type === "research" || e.event_type === "release");

  return (
    <div className="card-terminal p-4 space-y-3">
      <h3 className="font-mono text-xs text-accent tracking-widest">RESEARCH & RELEASES</h3>
      {research.length === 0 ? (
        <p className="font-mono text-xs text-muted">&gt; NO RESEARCH ITEMS</p>
      ) : (
        <ul className="space-y-2">
          {research.slice(0, 8).map((item) => (
            <li key={item.id} className="font-mono text-xs">
              {item.url ? (
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-accent">
                  {item.title}
                </a>
              ) : (
                item.title
              )}
              <span className="text-muted ml-2">{item.source}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
