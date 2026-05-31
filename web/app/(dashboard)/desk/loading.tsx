export default function DeskLoading() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 w-48 bg-surface-elevated rounded" />
      <div className="h-10 w-full bg-surface-elevated rounded" />
      <div className="grid md:grid-cols-2 gap-4">
        <div className="h-64 bg-surface-elevated rounded" />
        <div className="h-64 bg-surface-elevated rounded" />
        <div className="h-64 bg-surface-elevated rounded" />
        <div className="h-32 bg-surface-elevated rounded" />
      </div>
    </div>
  );
}
