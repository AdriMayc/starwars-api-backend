import { useState } from 'react';

interface JsonViewerProps {
  data: any;
}

export function JsonViewer({ data }: JsonViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border-b border-neutral-800">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 flex items-center justify-between hover:bg-neutral-800/50 transition-colors"
      >
        <h2 className="text-lg font-medium text-neutral-100">Raw JSON Response</h2>
        <span className="text-neutral-400 text-sm">{isExpanded ? '▼' : '▶'}</span>
      </button>
      {isExpanded && (
        <div className="px-6 pb-6">
          <pre className="bg-neutral-950 border border-neutral-800 rounded p-4 text-xs text-neutral-300 font-mono overflow-x-auto max-h-96 overflow-y-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
