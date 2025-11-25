# ToneCards Lab

A full-stack monorepo application for managing Chinese language flashcards, built with FastAPI (backend) and Svelte (frontend).

### 1. Setup Backend

```bash
cd tcl-api

uv sync

pip install -e .

uv run uvicorn tcl_api.main:app --reload

uvicorn tcl_api.main:app --reload
```

### 2. Generate Types for Frontend

```bash
cd tcl-api

uv run python scripts/generate_types.py

python scripts/generate_types.py
```

### 3. Setup Frontend

```bash
cd tcl-web

npm install

npm run generate-types

npm run dev
```

```bash
Make changes to the API code in tcl-api
cd tcl-api

uv run uvicorn tcl_api.main:app --reload

uv run python scripts/generate_types.py

cd ../tcl-web
npm run generate-types
```


## Configuration

Create a `.env` file in `tcl-api`:

```env
APP_NAME=ToneCards Lab API
APP_VERSION=0.1.0
DEBUG=true
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
HOST=0.0.0.0
PORT=8000
```

## Contributing

1. Make changes to the API
2. Regenerate OpenAPI spec
3. Regenerate TypeScript types
4. Update frontend code
5. Test both backend and frontend
6. Submit PR

### CORS errors

Ensure `CORS_ORIGINS` in `.env` includes your frontend URL.

