import { useEffect, useState } from "react";
import { Tabs } from "./components/Tabs";
import { SearchInput } from "./components/SearchInput";
import { Pagination } from "./components/Pagination";
import { ResourceList } from "./components/ResourceList";
import { DetailPanel } from "./components/DetailPanel";
import type { ResourceType, Resource, ApiEnvelope, RelatedItem } from "./types/api";
import {
  fetchResources,
  fetchRelated,
  buildRelatedPath,
  peekCachedEnvelope,
} from "./utils/api";

export default function App() {
  const [activeTab, setActiveTab] = useState<ResourceType>("films");
  const [searchQuery, setSearchQuery] = useState("");
  const [pageSize, setPageSize] = useState(10);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [response, setResponse] = useState<ApiEnvelope<Resource> | null>(null);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [relatedItems, setRelatedItems] = useState<RelatedItem[]>([]);
  const [relatedResponse, setRelatedResponse] =
    useState<ApiEnvelope<RelatedItem> | null>(null);

  // ---- LIST (com abort) ----
  useEffect(() => {
    const ac = new AbortController();

    (async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchResources(
          activeTab,
          page,
          pageSize,
          searchQuery,
          ac.signal
        );
        if (!ac.signal.aborted) setResponse(data);
      } catch (err: any) {
        if (err?.name !== "AbortError") setError("Failed to load resources");
      } finally {
        if (!ac.signal.aborted) setLoading(false);
      }
    })();

    return () => ac.abort();
  }, [activeTab, page, pageSize, searchQuery]);

  // Ao trocar tab, zera seleção e related
  useEffect(() => {
    setSelectedId(null);
    setRelatedItems([]);
    setRelatedResponse(null);
  }, [activeTab]);

  // ---- RELATED (cache instantâneo + abort) ----
  useEffect(() => {
    const ac = new AbortController();

    const canLoadRelated =
      selectedId != null && (activeTab === "films" || activeTab === "planets");

    if (!canLoadRelated) {
      setRelatedItems([]);
      setRelatedResponse(null);
      return () => ac.abort();
    }

    const path =
      activeTab === "films"
        ? buildRelatedPath("films", selectedId!, "characters")
        : buildRelatedPath("planets", selectedId!, "residents");

    // pinta instantâneo se tiver cache (sem flicker)
    const cached = peekCachedEnvelope<RelatedItem>(path);
    if (cached) {
      setRelatedItems(cached.data);
      setRelatedResponse(cached);
    } else {
      setRelatedItems([]);
      setRelatedResponse(null);
    }

    (async () => {
      try {
        if (activeTab === "films") {
          const data = await fetchRelated(
            "films",
            selectedId!,
            "characters",
            ac.signal
          );
          if (!ac.signal.aborted) {
            setRelatedItems(data.data);
            setRelatedResponse(data);
          }
        } else {
          const data = await fetchRelated(
            "planets",
            selectedId!,
            "residents",
            ac.signal
          );
          if (!ac.signal.aborted) {
            setRelatedItems(data.data);
            setRelatedResponse(data);
          }
        }
      } catch (err: any) {
        if (err?.name !== "AbortError") {
          console.error("Failed to load related items", err);
        }
      }
    })();

    return () => ac.abort();
  }, [selectedId, activeTab]);

  const handleTabChange = (tab: ResourceType) => {
    setActiveTab(tab);
    setPage(1);
    setSearchQuery("");
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPage(1);
  };

  const handlePageSizeChange = (value: number) => {
    setPageSize(value);
    setPage(1);
  };

  const selectedResource =
    response?.data.find((r) => r.id === selectedId) || null;

  const getRelatedLabel = () => {
    if (activeTab === "films") return "Characters";
    if (activeTab === "planets") return "Residents";
    return undefined;
  };

  return (
    <div className="min-h-screen bg-neutral-900 text-neutral-100">
      <header className="border-b border-neutral-800 bg-neutral-950">
        <div className="px-6 py-6">
          <h1 className="text-2xl font-medium text-neutral-100">
            Star Wars Explorer
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            API Explorer (Backend Python + GCP)
          </p>
        </div>

        <Tabs activeTab={activeTab} onTabChange={handleTabChange} />
      </header>

      <div className="border-b border-neutral-800 bg-neutral-950">
        <div className="px-6 py-4 flex flex-wrap items-center gap-4">
          <SearchInput value={searchQuery} onChange={handleSearchChange} />
          <select
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            className="bg-neutral-800 border border-neutral-700 rounded px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-neutral-500"
          >
            <option value={5}>page_size = 5</option>
            <option value={10}>page_size = 10</option>
            <option value={20}>page_size = 20</option>
            <option value={50}>page_size = 50</option>
          </select>

          <Pagination
            page={page}
            hasNext={!!response?.links.next}
            hasPrev={!!response?.links.prev}
            onPageChange={setPage}
          />
        </div>
      </div>

      <div className="flex flex-col lg:flex-row h-[calc(100vh-200px)]">
        <div className="w-full lg:w-2/5 border-r border-neutral-800 overflow-y-auto bg-neutral-950">
          <ResourceList
            resources={response?.data || []}
            selectedId={selectedId}
            onSelect={setSelectedId}
            loading={loading}
            error={error}
          />
        </div>

        <div className="w-full lg:w-3/5 bg-neutral-900 overflow-y-auto">
          <DetailPanel
            resource={selectedResource}
            resourceType={activeTab}
            relatedItems={relatedItems}
            relatedLabel={getRelatedLabel()}
            rawResponse={relatedResponse || response}
            requestId={response?.meta.request_id}
            selfLink={response?.links.self}
          />
        </div>
      </div>
    </div>
  );
}
