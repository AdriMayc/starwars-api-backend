import type { ResourceType } from '../types/api';

interface TabsProps {
  activeTab: ResourceType;
  onTabChange: (tab: ResourceType) => void;
}

const tabs: { id: ResourceType; label: string }[] = [
  { id: 'films', label: 'Films' },
  { id: 'people', label: 'People' },
  { id: 'planets', label: 'Planets' },
  { id: 'starships', label: 'Starships' },
];

export function Tabs({ activeTab, onTabChange }: TabsProps) {
  return (
    <div className="flex border-b border-neutral-700">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-6 py-3 font-medium text-sm transition-colors relative ${
            activeTab === tab.id
              ? 'text-neutral-100'
              : 'text-neutral-400 hover:text-neutral-200'
          }`}
        >
          {tab.label}
          {activeTab === tab.id && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-neutral-100" />
          )}
        </button>
      ))}
    </div>
  );
}
