# Deploy

## Backend (GCP — Cloud Run)

O backend é publicado em **Cloud Run** via **Buildpacks** (source deploy) e exposto publicamente via **API Gateway** (API Key em `x-api-key`).

### Deploy do Cloud Run
```powershell
gcloud config set project SEU_PROJECT_ID
gcloud run deploy starwars-api `
  --source . `
  --region us-central1 `
  --allow-unauthenticated
```

**Requisitos do repo**

- `requirements.txt` na raiz do repositório (mesmo nível do `Procfile`)
- `Procfile` com `PYTHONPATH=src` para imports `app.*`

**Exemplo de Procfile**:

```
web: PYTHONPATH=src python -m functions_framework --target main --source src/main.py --host 0.0.0.0 --port $PORT
```

**URL do Cloud Run**: após deploy, anote a URL gerada (ex: `https://starwars-api-abc123-uc.a.run.app`)

---

## API Gateway (rendered spec)

O API Gateway usa um spec **Swagger 2.0 rendered** com `x-google-backend` apontando para a URL do Cloud Run.

### Fluxo:

1. gerar/atualizar `openapi-gateway.rendered.yaml` substituindo a URL do backend
2. criar uma nova API config (configs são imutáveis)
3. atualizar o gateway para usar a config nova

**Sintoma típico de spec desatualizada**:
```json
{"message":"The current request is not defined by this API.","code":404}
```

### Comandos

```bash
# 1. Criar API config
gcloud api-gateway api-configs create CONFIG_ID_NOVO \
  --api=starwars-api \
  --openapi-spec=openapi-gateway.rendered.yaml \
  --project=SEU_PROJECT_ID \
  --backend-auth-service-account=SEU_SA@SEU_PROJECT_ID.iam.gserviceaccount.com

# 2. Atualizar gateway
gcloud api-gateway gateways update starwars-gw \
  --api=starwars-api \
  --api-config=CONFIG_ID_NOVO \
  --location=us-central1 \
  --project=SEU_PROJECT_ID
```

**URL do Gateway**: anote o hostname gerado (ex: `https://starwars-gw-7da2sx11.uc.gateway.dev`)

---

## Smoke test no Gateway

```powershell
# PowerShell
$key = "SUA_API_KEY"
Invoke-WebRequest -Uri "https://SEU_GW/health" -Headers @{ "x-api-key" = $key }
```

```bash
# Linux/Mac
curl -i -H "x-api-key: SUA_API_KEY" https://SEU_GW/health
```

---

## Frontend (Vercel)

Arquivo existente: `frontend/vercel.json`

**Rewrite**:

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://starwars-gw-7da2sx11.uc.gateway.dev/:path*" }
  ]
}
```

**Variáveis na Vercel**:

- `VITE_API_KEY` (usada em `frontend/src/utils/api.ts` como header `x-api-key`)

**Deploy**:

```bash
cd frontend
vercel --prod
```

---

## (Opcional) Script antigo — Cloud Functions Gen2

O arquivo `scripts/deploy_gcp.ps1` é um fluxo legado baseado em **Cloud Functions Gen2**.  
No estado final do repo, o deploy recomendado é via **Cloud Run**.
