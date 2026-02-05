# API (endpoints + envelope + exemplos)

Contrato: `src/openapi.yaml`

## Envelope padrão (implementação real)
No backend, o envelope é definido em `src/schemas/common.py`:

- `data`: payload (lista na prática nos endpoints atuais)
- `meta`: inclui `request_id` e, quando aplicável, `page/page_size/count/total`
- `links`: `self` obrigatório; `next/prev` quando aplicável
- `errors`: lista; no sucesso é `[]`

### Exemplo (sucesso)
```json
{
  "data": [{"id": 1, "name": "Luke Skywalker", "url": "https://swapi.dev/api/people/1/"}],
  "meta": { "request_id": "rid-123", "page": 1, "page_size": 10, "count": 1, "total": 82 },
  "links": { "self": "/people?page=1&page_size=10", "next": "/people?page=2&page_size=10", "prev": null },
  "errors": []
}
```

### Exemplo (erro)
```json
{
  "data": null,
  "meta": { "request_id": "rid-123" },
  "links": { "self": "/people?page=0" },
  "errors": [{ "code": "VALIDATION_ERROR", "message": "page must be >= 1", "details": null }]
}
```

## Endpoints

### Health

```
GET /health
```

### Listagens

```
GET /films
GET /people
GET /planets
GET /starships
```

Query params:

- `page` (default 1)
- `page_size` (default 10, max 50)
- `q` (busca)

### Correlacionados

```
GET /films/{id}/characters
GET /planets/{id}/residents
```

Query params:

- `page/page_size` (aplicados antes do fan-out)
- `q` (filtro local por name, aplicado após montar a janela)

## Exemplos (curl)

Produção (Gateway): incluir `x-api-key`  
Local (Function direta): não precisa

### People (window pagination)
```bash
curl -s \
  -H "x-api-key: $API_KEY" \
  "https://starwars-gw-7da2sx11.uc.gateway.dev/people?page=2&page_size=15&q=luke"
```

### Film characters (fan-out + cache TTL)
```bash
curl -s \
  -H "x-api-key: $API_KEY" \
  "https://starwars-gw-7da2sx11.uc.gateway.dev/films/1/characters?page=1&page_size=10"
```
