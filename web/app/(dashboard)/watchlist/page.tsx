import { WatchlistManager } from "@/components/WatchlistManager";

export default function WatchlistPage() {
  return (
    <div className="space-y-4">
      <div>
        <p className="badge-classified inline-block mb-2">TRACKING</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">WATCHLIST</h1>
        <p className="text-sm text-muted mt-1">
          Select providers, models, and workloads. Alerts filter to your selections.
        </p>
      </div>
      <WatchlistManager />
    </div>
  );
}
