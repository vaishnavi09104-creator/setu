export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton-wave rounded-md bg-slate-200 ${className}`} aria-hidden="true" />;
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-line bg-card p-4">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="mt-3 h-4 w-1/3" />
      <Skeleton className="mt-4 h-8 w-full" />
      <Skeleton className="mt-3 h-4 w-5/6" />
    </div>
  );
}

export function RowSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}
