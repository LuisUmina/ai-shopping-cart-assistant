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

Current coverage: **289 tests passing** (models, parsers, intent extraction, scraper base, store scrapers, filtering, ranking, cart builder, cart reasoning).

## Tiendas soportadas y metadatos

| Tienda | Método de extracción | Título | Marca | Categoría | Precio | Stock |
|--------|---------------------|:------:|:-----:|:---------:|:------:|:-----:|
| Plaza Vea | Playwright + `data-ga-*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tottus | Playwright + `__NEXT_DATA__` (Next.js) | ✅ | ✅ | ❌ | ✅ | — |
| Vivanda | Playwright + JSON-LD (`ItemList`) | ✅ | ✅ | ❌ | ✅ | ✅ |
| Metro | Playwright + selectores VTEX | ✅ | — | ❌ | ✅ | — |

## Motor de filtrado y ranking

### Filtrado (`FilteringService`)

Cada candidato recibe un score de relevancia [0, 1]. Los que quedan por debajo de **0.55** se descartan antes del ranking.

```
score = título    × 0.55
      + categoría × 0.10
      + marca     × 0.15
      + unidad    × 0.10
      + stock     × 0.10
      − penalización por keywords negativos (accesorios, utensilios…)
```

### Ranking (`RankingService`)

Los candidatos que superan el filtro se ordenan con una fórmula ponderada cuyos pesos varían según `price_priority` y `brand_priority` del usuario.

```
score_final =
    relevancia  × w_relevancia   (~35 %)
  + precio      × w_precio       (~25 %, sube con price_priority = high)
  + unidad      × w_unidad       (~15 %)
  + marca       × w_marca        (~15 %, sube con brand_priority = high)
  + stock       × w_stock        (~ 5 %)
  + tienda      × w_tienda       (~ 5 %)
```

La relevancia dentro del ranking se calcula así:

```
relevancia = título × 0.90 + bonus_categoría (máx. 0.10)
```

### Por qué la categoría tiene peso bajo (anti-sesgo)

Solo Plaza Vea expone metadatos de categoría estructurados (`data-ga-category`).
Las demás tiendas no tienen ese campo en su HTML. Si la categoría pesara mucho,
Plaza Vea siempre ganaría — no por tener el mejor producto, sino por tener más
metadatos en su página.

Diseño actual:

| Etapa | Peso de categoría | Efecto |
|-------|------------------|--------|
| Filtrado | 0.10 | Diferencia máxima de ±0.05 por categoría |
| Ranking | bonus ≤ 0.10 | Una diferencia de precio del 5 % ya invierte el resultado |

Con este diseño, Tottus, Metro y Vivanda compiten en igualdad de condiciones
cuando su precio o presentación es mejor.

### Carrito mixto vs. carrito de una sola tienda

El carrito es **mixto**: por cada ítem pedido se elige el mejor candidato global
sin importar de qué tienda venga. El arroz puede venir de Metro y la leche de
Vivanda si eso resulta más barato o más ajustado a lo pedido.

Una lógica de "elige la tienda más completa y compra todo ahí" no está
implementada en esta versión del MVP.

## Development phases

| Phase | Status | Description |
|---|---|---|
| 0 | ✅ Done | Project setup — FastAPI, React+Vite+Tailwind, /api/health |
| 1 | ✅ Done | Pydantic models — ProductCandidate, ShoppingIntent, UserPreferences, CartItem |
| 2 | ✅ Done | Deterministic parsers — price, unit (g→kg, ml→l), text cleaning, brand extraction |
| 3 | ✅ Done | Intent extraction — LLM call, Pydantic validation, prompt template, POST /api/chat |
| 4 | ✅ Done | Scraper base — BaseScraper (ABC + async ctx manager), Playwright, artifact saving |
| 5 | ✅ Done | Store scrapers — Plaza Vea, Metro, Tottus, Vivanda |
| 6 | ✅ Done | Pre-filtering engine — relevance scoring, negative keywords |
| 7 | ✅ Done | Ranking engine + cart builder — required units, price scoring, alternatives |
| 8 | ✅ Done | LLM final reasoning — compact candidate input, validated cart output |
| 9 | ✅ Done | Web interface — ChatPanel, PreferencesPanel, CartSummary, ProductCard |
| 10 | ⬜ Next | Demo scenario — end-to-end demo with real products |
