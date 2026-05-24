# AI Shopping Cart Assistant

Conversational web app that builds a supermarket shopping cart from natural language. It extracts shopping intent, scrapes Peruvian supermarket sites (Plaza Vea, Metro, Vivanda, Tottus), pre-filters and ranks products deterministically, and uses an LLM only for intent extraction and the final cart explanation.

See `ai_shopping_cart_assistant_mvp_plan.md` for the full MVP plan.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, Pydantic, Playwright
- **Frontend:** React + Vite + TypeScript + Tailwind CSS v4
- **LLM:** OpenAI API by default; OpenCode (OpenAI-compatible) also supported, switchable via env var

## Project structure

```
backend/        FastAPI app (api, models, services, scrapers, utils, db)
frontend/       React + Vite UI
data/           Scraping artifacts (raw_html, screenshots, raw/normalized JSON)
prompts/        LLM prompt templates
docs/           Architecture and notes
```

## Setup

### 1. Environment variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

Set `LLM_PROVIDER` to `openai` or `opencode` and fill the matching keys.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Health check: http://localhost:8000/api/health

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 (shows the live backend health status).

## Development phases

The project is built in phases (see the plan). **Phase 0 (setup) is complete:** folder structure, FastAPI health endpoint, frontend base UI, and shared configuration.
