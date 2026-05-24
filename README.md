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

## Running tests

```bash
cd backend
.venv\Scripts\python.exe -m pytest tests/ -v
```

Current coverage: **172 tests passing** (models, parsers, intent extraction, scraper base, store scrapers).

## Development phases

| Phase | Status | Description |
|---|---|---|
| 0 | ✅ Done | Project setup — FastAPI, React+Vite+Tailwind, /api/health |
| 1 | ✅ Done | Pydantic models — ProductCandidate, ShoppingIntent, UserPreferences, CartItem |
| 2 | ✅ Done | Deterministic parsers — price, unit (g→kg, ml→l), text cleaning, brand extraction |
| 3 | ✅ Done | Intent extraction — LLM call, Pydantic validation, prompt template, POST /api/chat |
| 4 | ✅ Done | Scraper base — BaseScraper (ABC + async ctx manager), Playwright, artifact saving |
| 5 | ✅ Done | Store scrapers — Plaza Vea, Metro, Tottus, Vivanda |
| 6 | ⬜ Next | Pre-filtering engine — relevance scoring, negative keywords |
| 7 | ⬜ | Ranking engine + cart builder — required units, price scoring, alternatives |
| 8 | ⬜ | LLM final reasoning — compact candidate input, validated cart output |
| 9 | ⬜ | Web interface — ChatPanel, PreferencesPanel, CartSummary, ProductCard |
| 10 | ⬜ | Demo scenario — end-to-end demo with real products |
