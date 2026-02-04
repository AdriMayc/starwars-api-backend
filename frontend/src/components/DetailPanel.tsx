import type { Resource } from '../types/api';
import { RelatedList } from './RelatedList';
import { JsonViewer } from './JsonViewer';

interface DetailPanelProps {
  resource: Resource | null;
  relatedItems?: Array<{ id: number; name: string }>;
  relatedLabel?: string;
  rawResponse?: any;
  requestId?: string;
  selfLink?: string;
}

export function DetailPanel({
  resource,
  relatedItems,
  relatedLabel,
  rawResponse,
  requestId,
  selfLink,
}: DetailPanelProps) {
  if (!resource) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-neutral-500 text-sm">Select an item to view details</div>
      </div>
    );
  }

  const name = 'title' in resource ? resource.title : 'name' in resource ? resource.name : '';

  const getDisplayFields = (): Array<{ label: string; value: string }> => {
    const exclude = ['id', 'url', 'name', 'title'];
    return Object.entries(resource)
      .filter(([key]) => !exclude.includes(key))
      .map(([key, value]) => ({
        label: key
          .split('_')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' '),
        value: String(value),
      }));
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Basic Information */}
      <div data-testid="basic-info" className="p-6 border-b border-neutral-800">
        <h2 className="text-lg font-medium text-neutral-100 mb-4">Basic Information</h2>
        <div className="space-y-3">
          <div className="flex">
            <span className="text-sm text-neutral-500 w-20">ID</span>
            <span className="text-sm text-neutral-100 font-mono">#{resource.id}</span>
          </div>
          <div className="flex">
            <span className="text-sm text-neutral-500 w-20">Name</span>
            <span className="text-sm text-neutral-100">{name}</span>
          </div>
          <div className="flex">
            <span className="text-sm text-neutral-500 w-20">URL</span>
            <span className="text-sm text-neutral-400 font-mono break-all">{resource.url}</span>
          </div>
        </div>
      </div>

      {/* Additional Fields */}
      <div className="p-6 border-b border-neutral-800">
        <h2 className="text-lg font-medium text-neutral-100 mb-4">Details</h2>
        <div className="space-y-3">
          {getDisplayFields().map((field, index) => (
            <div key={index} className="flex">
              <span className="text-sm text-neutral-500 w-40 shrink-0">{field.label}</span>
              <span className="text-sm text-neutral-300">{field.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Related Items */}
      {relatedItems && relatedItems.length > 0 && relatedLabel && (
        <div className="p-6 border-b border-neutral-800">
          <h2 className="text-lg font-medium text-neutral-100 mb-4">{relatedLabel}</h2>
          <RelatedList items={relatedItems} />
        </div>
      )}

      {/* Raw JSON Response */}
      {rawResponse && <JsonViewer data={rawResponse} />}

      {/* Technical Info */}
      {(requestId || selfLink) && (
        <div className="p-6 bg-neutral-900/50">
          <h3 className="text-xs font-medium text-neutral-500 uppercase mb-3">Technical Info</h3>
          <div className="space-y-2">
            {requestId && (
              <div className="flex flex-col">
                <span className="text-xs text-neutral-600">Request ID</span>
                <span className="text-xs text-neutral-400 font-mono">{requestId}</span>
              </div>
            )}
            {selfLink && (
              <div className="flex flex-col">
                <span className="text-xs text-neutral-600">Self Link</span>
                <span className="text-xs text-neutral-400 font-mono break-all">{selfLink}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
