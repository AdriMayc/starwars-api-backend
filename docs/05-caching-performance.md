# Caching e performance

## Backend

### 1) httpx.Client reutilizável (keep-alive)
Implementação: `src/clients/swapi.py`
- `SwapiClient._get_client()` cria um `httpx.Client` uma vez e reusa na instância.
- Em Cloud Functions, isso reduz overhead dentro do mesmo container (warm starts).

### 2) Retry + backoff
Implementação: `src/clients/swapi.py`
- `RetryConfig`:
  - `max_retries=2`
  - `backoff_base=0.2`
  - `backoff_factor=2.0`
  - retry em: `429, 500, 502, 503, 504`
- Timeout: `3s`

### 3) Cache TTL para fan-out (`get_by_url`)
Implementação: `src/clients/swapi.py`
- `get_by_url(url)` cacheia por chave: `url + params`
- TTL default: `300s` (`by_url_cache_ttl`)
- Motivação: endpoints correlacionados (`/films/{id}/characters`, `/planets/{id}/residents`) fazem fan-out de várias URLs.

### 4) Fan-out bounded
Implementação: `src/app/concurrency.py` + handlers correlacionados
- `run_bounded(fn, items, max_workers=8)` controla concorrência.

---

## Frontend

Implementação: `frontend/src/utils/api.ts`

### 1) Cache in-memory (TTL)
- TTL default: `60s`
- cache key inclui API key (`VITE_API_KEY`) para não misturar identidades.

### 2) In-flight dedupe
- `inFlight` (Map) garante que duas chamadas concorrentes pro mesmo path compartilhem a mesma Promise.

### 3) Abort por consumidor
- `withAbort(p, signal)` faz `Promise.race`:
  - um consumidor pode abortar sua espera sem cancelar o fetch compartilhado
  - quando o fetch termina, o cache pode ser preenchido para chamadas futuras
