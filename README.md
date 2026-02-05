# Star Wars Explorer — Backend (GCP) + Frontend (Vercel)

Plataforma para explorar dados de Star Wars consumindo a **SWAPI** e expondo um contrato próprio com:
- **Backend (Python 3.11)** rodando em **Cloud Run** e protegido por **API Gateway** com **API Key** (`x-api-key`).
- **Frontend (Vite + React)** com cache/dedupe/abort no client e deploy na **Vercel**.

> Upstream: `https://swapi.dev/api`

## Links rápidos
- Documentação (detalhada):
  - [Contexto e objetivos](docs/00-context.md)
  - [Arquitetura (GCP + Vercel) + Mermaid](docs/01-architecture.md)
  - [Rodar local (backend + frontend)](docs/02-local-dev.md)
  - [API: endpoints + envelope + exemplos](docs/03-api.md)
  - [Paginação e filtros (window vs SWAPI=10)](docs/04-pagination-filtering.md)
  - [Caching e performance (backend + frontend)](docs/05-caching-performance.md)
  - [Segurança (API Key / referrer)](docs/06-security.md)
  - [Testes (pytest/respx + vitest)](docs/07-testing.md)
  - [Deploy (GCP + Vercel)](docs/08-deploy.md)
  - [Observabilidade e erros](docs/09-observability-errors.md)
  - [Decisões, trade-offs e próximos passos](docs/10-decisions-tradeoffs-nextsteps.md)
  - [Deploy e Troubleshooting](docs/11-deploy-troubleshooting.md)
- ADRs (Architecture Decision Records):
  - [ADR 001: Cloud Run + API Gateway como backend público](docs/adr/001-cloud-run-api-gateway.md)

## Endpoints principais (backend)
- `GET /health`
- `GET /films`
- `GET /people`
- `GET /planets`
- `GET /starships`
- `GET /films/{id}/characters`
- `GET /planets/{id}/residents`

Contrato OpenAPI (backend): [`src/openapi.yaml`](src/openapi.yaml)  
Spec do API Gateway (template): [`openapi-gateway.yaml`](openapi-gateway.yaml)  
> O arquivo `openapi-gateway.rendered.yaml` é gerado no deploy substituindo a URL do backend e não é versionado.


## Quickstart local

### Backend
```bash
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# IMPORTANTE: o código está em src/, então precisamos do PYTHONPATH=src
# Windows PowerShell:
$env:PYTHONPATH="src"
functions-framework --target main --source src/main.py --port 8080

# Linux/Mac:
# PYTHONPATH=src functions-framework --target main --source src/main.py --port 8080


### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Produção (já preparado no repo)

Vercel rewrite: `frontend/vercel.json` reescreve `/api/*` para o hostname do Gateway:

```
https://starwars-gw-7da2sx11.uc.gateway.dev/*
```

API Key (browser): configure `VITE_API_KEY` na Vercel.

---

## Deploy (Cloud Run)

O projeto roda em **Cloud Run** via **Buildpacks**.

⚠️ **Requisitos críticos**:

1. **requirements.txt deve ficar na raiz do repositório** (mesmo nível do `Procfile`).
   - Caso contrário, as dependências não são instaladas e o container falha com `No module named functions_framework`.

2. **PYTHONPATH=src é necessário** para importar `app.*` quando o código está em `src/`.

**Exemplo de Procfile correto**:
```
web: PYTHONPATH=src python -m functions_framework --target main --source src/main.py --host 0.0.0.0 --port $PORT
```

### API Gateway (Swagger rendered)

O API Gateway é configurado com um arquivo **rendered** (Swagger 2.0) contendo `x-google-backend`.

⚠️ **Rotas adicionadas no `src/openapi.yaml` precisam existir também no `openapi-gateway.rendered.yaml`**.

**Sintoma típico de spec desatualizada**:
```json
{"message":"The current request is not defined by this API.","code":404}
```
→ rota não publicada no gateway config.

### Vercel

⚠️ **`vercel.json` rewrites apenas reescrevem URL**; não adicionam headers.

Chamadas ao gateway precisam incluir `x-api-key` no client do frontend, ou implementar proxy server-side.

**Configuração atual**: `VITE_API_KEY` enviado diretamente do browser (API Key restrita por HTTP Referrer no GCP).

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---------|---------------|---------|
| `No module named functions_framework` | `requirements.txt` não na raiz | Mover `requirements.txt` para raiz |
| `No module named app` | `PYTHONPATH` não configurado | Adicionar `PYTHONPATH=src` no `Procfile` |
| Gateway 404 "not defined by this API" | Rota não no rendered spec | Re-deploy da API config com spec atualizado |
| Frontend não autentica | `x-api-key` não enviado | Verificar `VITE_API_KEY` na Vercel |

Veja [Deploy e Troubleshooting](docs/11-deploy-troubleshooting.md) para detalhes completos.