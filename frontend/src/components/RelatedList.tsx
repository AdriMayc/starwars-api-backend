interface RelatedListProps {
  items: Array<{ id: number; name: string }>;
}

export function RelatedList({ items }: RelatedListProps) {
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center gap-3 px-3 py-2 bg-neutral-800/50 rounded"
        >
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-neutral-700 text-neutral-300">
            #{item.id}
          </span>
          <span className="text-sm text-neutral-300">{item.name}</span>
        </div>
      ))}
    </div>
  );
}
