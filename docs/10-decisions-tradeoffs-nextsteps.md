# Decisões técnicas, trade-offs e próximos passos

## Decisões implementadas no repo
- Envelope padrão com Pydantic (`src/schemas/common.py`) e `extra="forbid"`
- Mini-router testável com path params (`src/app/router.py`)
- Window pagination para SWAPI fixa em 10 (`src/app/swapi_window.py`)
- Fan-out bounded (ThreadPool) para correlacionados (`src/app/concurrency.py`)
- Cache TTL em `get_by_url` para reduzir fan-out repetido (`src/clients/swapi.py`)
- Frontend com cache/dedupe/abort para UX e evitar tempestade de requests (`frontend/src/utils/api.ts`)
- Vercel rewrite de `/api/*` para o gateway (`frontend/vercel.json`)

## Trade-offs (conscientes)
- Cache in-memory (backend e frontend):
  - não compartilhado entre instâncias; reseta em cold start
- `q` nos correlacionados:
  - aplicado após paginação; `total` reflete o total de URLs no relacionamento, não total pós-filtro
- `films`:
  - paginação é local após 1 chamada (adequado porque filmes são poucos)

## Próximos passos (incrementos naturais)
- corrigir/automatizar `x-google-backend` no OpenAPI do gateway para deixar o deploy script 100% reprodutível
- adicionar rate limit/quota no Gateway
- logs estruturados com latência upstream, cache hit/miss e request_id
- cache HTTP (ETag / Cache-Control) e/ou CDN para listagens
