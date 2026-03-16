Railway deployment plan for Story Engine MK2

Services
- `backend`: Docker build from repo root using `backend/Dockerfile`
- `frontend`: Docker build from `frontend/Dockerfile`
- `postgres`: Railway PostgreSQL service

Backend variables
- `DATABASE_URL`: reference Railway Postgres connection string
- `LLM_PROVIDER=openai`
- `LLM_EXTERNAL_ENABLED=true`
- `OPENAI_API_KEY=...`
- `OPENAI_BASE_URL=https://api.openai.com/v1`
- `LLM_MODEL_CHARACTER=gpt-4o-mini`
- `LLM_MODEL_SUMMARY=gpt-4o-mini`
- `LLM_MODEL_NARRATIVE=gpt-4o`

Frontend variables
- `VITE_API_BASE=https://<your-backend-public-domain>`

Notes
- Backend now listens on Railway `PORT`.
- Frontend now builds a production bundle and serves it with `vite preview`.
- Frontend API base is injected at build time through `VITE_API_BASE`.
