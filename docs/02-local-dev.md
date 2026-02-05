# Como rodar localmente (backend + frontend)

## Pré-requisitos
- Python 3.11+
- Node 18+

---

## Backend (Functions Framework) local

### Instalar dependências
```bash
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Subir o backend
O código está em `src/`, então é necessário `PYTHONPATH=src` para imports `app.*`.

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH="src"
functions-framework --source src/main.py --target main --port 8080
```

**Linux/Mac**

```bash
PYTHONPATH=src functions-framework --source src/main.py --target main --port 8080
```

### Testar
```bash
curl -i http://127.0.0.1:8080/health
```

> Em local você chama o backend direto (sem API Gateway), então API Key não é exigida.

---

## Frontend (Vite/React) local

### Instalar / rodar
```bash
cd frontend
npm install
npm run dev
```

### Como o frontend resolve /api/* em dev
O `frontend/vite.config.ts` configura proxy:

```
/api/films → http://127.0.0.1:8080/films (rewrite remove /api)
```

Por padrão, o target é `http://127.0.0.1:8080`.
Você pode sobrescrever com `VITE_API_BASE_URL`.

### Variáveis de ambiente (frontend)
Crie `frontend/.env.local`:

```bash
# em dev local sem gateway, pode ficar vazio
VITE_API_KEY=

# altera o target do proxy do Vite
VITE_API_BASE_URL=http://127.0.0.1:8080
```

---

## Endpoints correlacionados (exemplos)

```
GET /films/1/characters?page=1&page_size=10
GET /planets/1/residents?page=1&page_size=10
```
