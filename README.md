# LLM_ml

Personal LLM workbench for chat, skill retrieval, and tool-style web search.

## Stack

- `backend/`: Python FastAPI service for LLM providers, skill search, and tool APIs.
- `web/`: Next.js + React frontend workbench.
- `skills/`: public sample skill files.
- `docs/`: local-only project notes, intentionally ignored by Git.

## Quick Start

Backend:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Configuration

Copy `.env.example` to `.env` and fill provider secrets locally. Do not commit `.env`.

Model definitions live in `backend/app/config/models.example.json` by default. Add new providers by adding model config and, when needed, a provider adapter under `backend/app/services/llm/`.

For local paid/API testing, keep secrets in `.env` and optionally point `LLM_CONFIG_PATH` to an ignored `backend/app/config/models.local.json`.

Known OpenAI-compatible provider bases:

- DeepSeek: `https://api.deepseek.com`
- Gitee AI serverless: `https://ai.gitee.com/v1`

## API Surface

- `GET /api/health`
- `GET /api/models`
- `POST /api/chat`
- `POST /api/skills/search`
- `POST /api/tools/search-web`

The current default model `demo-local` is a local echo adapter so the workbench can run before real LLM API keys are provided.
