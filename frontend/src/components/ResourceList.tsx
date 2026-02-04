import type { Resource } from '../types/api';

interface ResourceListProps {
  resources: Resource[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  loading: boolean;
  error: string | null;
}

export function ResourceList({
  resources,
  selectedId,
  onSelect,
  loading,
  error,
}: ResourceListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-neutral-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-red-400 text-sm">{error}</div>
      </div>
    );
  }

  if (resources.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-neutral-500 text-sm">No results</div>
      </div>
    );
  }

  return (
    <div className="divide-y divide-neutral-800">
      {resources.map((resource) => {
        const name = 'title' in resource ? resource.title : 'name' in resource ? resource.name : '';
        const isSelected = resource.id === selectedId;

        return (
          <button
            key={resource.id}
            onClick={() => onSelect(resource.id)}
            className={`w-full text-left px-4 py-3 transition-colors ${
              isSelected
                ? 'bg-neutral-700 border-l-2 border-neutral-100'
                : 'hover:bg-neutral-800'
            }`}
          >
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${
                  isSelected
                    ? 'bg-neutral-600 text-neutral-100'
                    : 'bg-neutral-800 text-neutral-400'
                }`}
              >
                #{resource.id}
              </span>
              <span className={`text-sm ${isSelected ? 'text-neutral-100' : 'text-neutral-300'}`}>
                {name}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
