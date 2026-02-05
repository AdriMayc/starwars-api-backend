# Contexto e objetivos

Este projeto implementa uma plataforma "Star Wars Explorer" para consumo de dados da **SWAPI** e exposição de um contrato próprio (backend), além de uma SPA (frontend) para navegar e depurar os endpoints.

## Objetivos do backend
- Expor endpoints de listagem (`films`, `people`, `planets`, `starships`) com:
  - paginação `page/page_size` (até 50)
  - busca `q` (mapeada para `search` na SWAPI em listagens)
  - envelope padrão `{data, meta, links, errors}`
- Expor endpoints correlacionados:
  - `GET /films/{id}/characters` (fan-out de URLs)
  - `GET /planets/{id}/residents` (fan-out de URLs)
- Resiliência:
  - timeout e retry/backoff em chamadas à SWAPI
  - mapear erros upstream para códigos HTTP e `errors[].code` consistentes
- Performance:
  - `httpx.Client` reutilizado (keep-alive)
  - cache TTL para `get_by_url` (fan-out)

## Objetivos do frontend
- Consumir `/api/*` (proxy em dev + rewrite em prod)
- Normalizar erros e exibir envelope de forma "debugável"
- Implementar:
  - cache in-memory (TTL)
  - dedupe de requisições concorrentes (in-flight)
  - abort por consumidor (sem cancelar o request compartilhado)
