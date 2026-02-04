interface PaginationProps {
  page: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, hasNext, hasPrev, onPageChange }: PaginationProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={!hasPrev}
        className="px-3 py-2 text-sm bg-neutral-800 border border-neutral-700 rounded text-neutral-100 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neutral-700 disabled:hover:bg-neutral-800 transition-colors"
      >
        Prev
      </button>
      <span className="text-sm text-neutral-400 font-mono">page = {page}</span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={!hasNext}
        className="px-3 py-2 text-sm bg-neutral-800 border border-neutral-700 rounded text-neutral-100 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neutral-700 disabled:hover:bg-neutral-800 transition-colors"
      >
        Next
      </button>
    </div>
  );
}
