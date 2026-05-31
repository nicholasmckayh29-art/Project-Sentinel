export default function FeedLoading() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 w-40 bg-surface-elevated rounded" />
      <div className="h-16 bg-surface-elevated rounded" />
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="h-72 bg-surface-elevated rounded" />
        <div className="h-72 bg-surface-elevated rounded" />
      </div>
      <div className="h-24 bg-surface-elevated rounded" />
    </div>
  );
}
