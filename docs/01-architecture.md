# Arquitetura (GCP Cloud Functions + API Gateway + Vercel)

## Componentes reais no repo
- Backend: `src/` (Cloud Functions Gen2 / Flask Request handler)
- Gateway: `openapi-gateway.yaml` (security apiKey + `$ref` para `src/openapi.yaml`)
- Frontend: `frontend/` (Vite/React)
- Vercel rewrite: `frontend/vercel.json`

## Diagrama (Mermaid)

```mermaid
flowchart LR
  U[Browser] --> V[Vercel (Vite/React)]
  V -->|/api/* (rewrite)| G[API Gateway (GCP)]
  G -->|x-api-key| F[Cloud Function Gen2 (Python/Flask handler)]
  F -->|HTTP| S[SWAPI swapi.dev]

  subgraph Backend["Backend (src/)"]
    F --> R[Mini-router + handlers]
    R --> E[Envelope {data, meta, links, errors}]
    R --> H[httpx.Client keep-alive]
    R --> C[Cache TTL get_by_url]
    R --> W[Window pagination sobre SWAPI=10]
    R --> X[Fan-out bounded (ThreadPool)]
  end

  subgraph Frontend["Frontend (frontend/)"]
    V --> FC[Cache TTL + inFlight dedupe + abort per-consumer]
  end
```

## Fluxo (request/response)

Browser chama `GET /api/people?page=1&page_size=20&q=luke`

1. Em produção: Vercel rewrite → Gateway
2. Gateway valida `x-api-key`
3. Gateway encaminha para a Function
4. Function chama SWAPI com timeout/retry, aplica paginação local/window, retorna envelope
