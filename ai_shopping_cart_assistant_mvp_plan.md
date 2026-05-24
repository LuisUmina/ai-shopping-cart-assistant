# AI Shopping Cart Assistant — MVP Development Plan

## 1. Project Objective

Build an **AI-powered shopping cart assistant** that helps a user create a supermarket shopping cart from natural language instructions.

The assistant must:

1. Understand the user's shopping request in conversational language.
2. Extract structured shopping intents: products, quantities, units, brands, substitutions, preferences, constraints.
3. Search products across a limited set of Peruvian supermarket websites.
4. Scrape and normalize product data into a clean JSON format.
5. Pre-filter irrelevant results before sending anything to the LLM.
6. Rank product candidates according to user preferences.
7. Propose an optimized cart.
8. Preserve product links so the user can open each selected item and manually complete the purchase.
9. Optionally support logged-in browsing later, but **not as a critical MVP requirement**.

The MVP is **not a full checkout automation system**. It is a **shopping cart recommendation and preparation assistant**.

---

## 2. MVP Scope

### 2.1 Included in MVP

The MVP must support:

- A simple web interface with:
  - Chat input.
  - User preference panel.
  - Product results preview.
  - Recommended cart summary.
  - Product links.
- Natural language request parsing.
- Persistent user preferences.
- Web scraping using **Playwright CLI workflow**.
- Initial supermarket targets:
  - Plaza Vea.
  - Metro.
  - Vivanda.
  - Tottus.
- Product search per item, not full catalog crawling.
- Product data extraction into normalized JSON.
- Pre-filtering engine before LLM reasoning.
- Ranking engine based on price, brand, unit price, quantity match, availability and relevance.
- Basic substitution logic:
  - Example: if the user asks for 1 liter and only 500 ml is available, suggest 2 units of 500 ml.
  - Example: if the user asks for 5 kg of rice and only 1 kg bags are available, suggest 5 units.
- Cart proposal with:
  - Selected product.
  - Store.
  - Unit price.
  - Total quantity.
  - Required units.
  - Total estimated cost.
  - Reason for selection.
  - Product URL.

---

### 2.2 Explicitly Out of Scope for MVP

Do **not** implement the following in MVP:

- Automatic payment.
- Automatic checkout.
- Full account management.
- Production-grade login/session handling.
- Real-time inventory guarantees.
- Price history tracking.
- Coupon optimization.
- Multi-user authentication.
- Mobile app.
- Browser extension.
- Full product catalog database.
- Automated purchase confirmation.
- Complex nutritional analysis.
- Computer vision-based product recognition.
- Large-scale distributed scraping.
- Advanced recommendation engine based on historical purchases.

These can be considered future extensions, but must not block the MVP.

---

## 3. Core User Flow

```text
1. User opens web app.
2. User configures or confirms shopping preferences.
3. User writes a natural language request:
   "Necesito 5 kg de arroz, 2 litros de leche gloria y papel higiénico barato."
4. The assistant extracts structured shopping intents.
5. The system searches each product across supported stores.
6. Playwright scrapers collect product candidates.
7. The system normalizes all products into a standard JSON schema.
8. The pre-filtering engine removes irrelevant products.
9. The ranking engine scores the remaining candidates.
10. The LLM only receives compact, pre-filtered candidates.
11. The assistant proposes a cart.
12. User reviews alternatives and selected products.
13. User opens product links manually.
```

---

## 4. Important Design Principle

The LLM must **not** receive raw scraping dumps.

Do **not** send 200+ products per store per item to the LLM.

The system must follow this pipeline:

```text
Raw Search Results
      ↓
HTML Extraction
      ↓
Normalized Product JSON
      ↓
Deterministic Pre-filtering
      ↓
Top-N Candidate Selection
      ↓
LLM Reasoning
      ↓
Final Cart Recommendation
```

The LLM should only receive:

- User intent.
- User preferences.
- A compact list of top product candidates.
- Ranking explanation data.
- Missing-information questions if needed.

Target:

```text
Maximum candidates sent to LLM:
- 5 to 10 candidates per requested product.
- Prefer 5 for MVP.
```

---

## 5. Functional Requirements

### FR-001 — Conversational Input

The system must allow the user to enter a shopping request in natural language.

Examples:

```text
"Quiero comprar arroz, leche y detergente. Prioriza precios bajos."
"Necesito 5 kg de arroz costeño y 2 litros de leche sin lactosa."
"Arma una compra semanal para desayuno con marcas conocidas."
"Compra lo más barato, pero evita marcas desconocidas."
```

The assistant must extract:

- Product name.
- Quantity.
- Unit.
- Brand preference.
- Quality preference.
- Price preference.
- Substitution tolerance.
- Store preference, if any.
- Constraints or exclusions.

---

### FR-002 — User Preferences / Memory

The system must store reusable user preferences.

Initial configurable preferences:

```json
{
  "price_priority": "high",
  "brand_priority": "medium",
  "known_brands_only": false,
  "allow_substitutions": true,
  "allow_equivalent_sizes": true,
  "preferred_stores": ["plaza_vea", "metro", "vivanda", "tottus"],
  "excluded_brands": [],
  "preferred_brands": [],
  "max_candidates_per_product": 5
}
```

Preference examples:

```text
"Siempre prioriza precios bajos."
"Prefiero marcas conocidas aunque cuesten un poco más."
"No me sugieras marcas desconocidas."
"Si no hay presentación exacta, permite equivalencias."
```

Storage for MVP:

- Use local JSON file or SQLite.
- Do not overengineer user profiles.
- Suggested MVP: `data/user_preferences.json`.

---

### FR-003 — Intent Extraction

The system must convert the user's request into structured intent.

Example input:

```text
"Necesito 5 kilos de arroz, 2 litros de leche Gloria y 1 detergente barato."
```

Expected structured output:

```json
{
  "shopping_intent": [
    {
      "raw_text": "5 kilos de arroz",
      "product_query": "arroz",
      "quantity": 5,
      "unit": "kg",
      "brand_preference": null,
      "price_sensitivity": "medium",
      "allow_substitution": true
    },
    {
      "raw_text": "2 litros de leche Gloria",
      "product_query": "leche",
      "quantity": 2,
      "unit": "l",
      "brand_preference": "Gloria",
      "price_sensitivity": "medium",
      "allow_substitution": true
    },
    {
      "raw_text": "1 detergente barato",
      "product_query": "detergente",
      "quantity": 1,
      "unit": "unit",
      "brand_preference": null,
      "price_sensitivity": "high",
      "allow_substitution": true
    }
  ]
}
```

Implementation options:

- Use OpenAI API for intent extraction.
- Add a deterministic post-processing validator.
- Use Pydantic models to validate structure.
- If OpenCode-compatible agents are available, use them for implementation support, not as core runtime dependency unless necessary.

---

### FR-004 — Store Search

The system must search products across:

- Plaza Vea.
- Metro.
- Vivanda.
- Tottus.

Search strategy:

1. Search broad product name first.
   - Example: search `"arroz"`, not `"5kg arroz"`.
2. Scrape product cards from search results.
3. Extract product details from listings.
4. Optionally visit product detail pages only when required.

Do not search directly for:

```text
"5 kg arroz"
"2 litros leche gloria"
```

Reason:

Store search engines behave inconsistently. Some use “kg”, others “kilo”, “x 1kg”, “1000 g”, “pack”, “caja”, etc.

Search broad, then normalize.

---

### FR-005 — Playwright CLI-Based Scraping

The implementation must use **Playwright through CLI-oriented workflows** and consult the available **Playwright CLI skill/documentation** before implementing scrapers.

Expected workflow per store:

1. Open the target website with Playwright.
2. Search product term.
3. Download/snapshot the HTML.
4. Take screenshots when selectors or results are unclear.
5. Inspect DOM and identify stable selectors.
6. Extract product data.
7. Save raw snapshots for debugging.
8. Convert extracted data to normalized JSON.

Important requirements:

- Do not rely only on brittle CSS selectors.
- Prefer robust locators when available.
- Save HTML snapshots during scraper development.
- Save screenshots to validate layout and result accuracy.
- Each scraper must be isolated per store.
- Scrapers must fail gracefully.

Development artifacts:

```text
data/raw_html/{store}/{query_timestamp}.html
data/screenshots/{store}/{query_timestamp}.png
data/raw_json/{store}/{query_timestamp}.json
```

---

### FR-006 — Product JSON Schema

Every scraped product must be normalized into this schema:

```json
{
  "store": "plaza_vea",
  "product_id": "optional_store_specific_id",
  "title": "Arroz Costeño Extra Bolsa 5 kg",
  "brand": "Costeño",
  "category": "arroz",
  "raw_price": "S/ 24.90",
  "price": 24.90,
  "currency": "PEN",
  "presentation_text": "Bolsa 5 kg",
  "quantity_value": 5,
  "quantity_unit": "kg",
  "unit_price": 4.98,
  "unit_price_unit": "kg",
  "availability": "available",
  "image_url": "https://...",
  "product_url": "https://...",
  "search_query": "arroz",
  "scraped_at": "2026-05-24T00:00:00-05:00",
  "confidence": {
    "brand_extraction": 0.9,
    "quantity_extraction": 0.95,
    "price_extraction": 1.0
  }
}
```

Minimum required fields for MVP:

```text
store
title
price
currency
presentation_text
quantity_value
quantity_unit
unit_price
availability
product_url
search_query
scraped_at
```

---

### FR-007 — Unit Normalization

The system must normalize product units.

Supported MVP units:

```text
Mass:
- g
- kg

Volume:
- ml
- l

Count:
- unit
- pack
- roll
- bag
- box
```

Normalization rules:

```text
1000 g = 1 kg
500 g = 0.5 kg
1000 ml = 1 l
500 ml = 0.5 l
```

Examples:

```text
"Arroz 750g" → quantity_value: 0.75, quantity_unit: "kg"
"Leche 900ml" → quantity_value: 0.9, quantity_unit: "l"
"Pack x 6 unidades" → quantity_value: 6, quantity_unit: "unit"
```

---

### FR-008 — Product Relevance Filtering

Before ranking, remove irrelevant products.

Example: if the user asks for `"arroz"`, the system must avoid irrelevant products such as:

```text
copas
tapers
recetarios
snacks unrelated to rice
```

Filtering strategy:

Use a combination of:

1. Keyword matching.
2. Category hints.
3. Title token matching.
4. Negative keywords.
5. Brand/presentation parsing.
6. Optional lightweight semantic check.

For MVP, implement deterministic scoring first.

Example relevance score:

```text
relevance_score =
  product_name_match * 0.40 +
  category_match * 0.25 +
  brand_match * 0.15 +
  unit_match * 0.10 +
  negative_keyword_penalty
```

Reject product if:

```text
relevance_score < 0.55
```

---

### FR-009 — Equivalent Quantity Logic

The system must calculate how many units are needed to satisfy the requested quantity.

Example:

```text
User wants: 5 kg arroz
Product A: 1 kg bag, S/ 5.20
Required units: 5
Total price: S/ 26.00

Product B: 5 kg bag, S/ 24.90
Required units: 1
Total price: S/ 24.90
```

Formula:

```text
required_units = ceil(requested_quantity / product_quantity)
total_price = required_units * product_price
effective_quantity = required_units * product_quantity
excess_quantity = effective_quantity - requested_quantity
```

The ranking must penalize excessive overbuying.

Example:

```text
User wants 1 liter.
Product is 3 liters.
Possible but penalized.
```

---

### FR-010 — Ranking Engine

The system must score product candidates using deterministic logic before LLM reasoning.

Suggested ranking score:

```text
final_score =
  relevance_score * 0.35 +
  price_score * 0.25 +
  unit_match_score * 0.15 +
  brand_score * 0.15 +
  availability_score * 0.05 +
  store_preference_score * 0.05
```

If the user says:

```text
"prioriza barato"
```

Increase price_score weight.

If the user says:

```text
"prefiero marcas conocidas"
```

Increase brand_score weight.

If the user says:

```text
"quiero exactamente 5 kg"
```

Increase unit_match_score and penalize substitutions.

---

### FR-011 — LLM Cart Reasoning

The LLM should receive only compact structured candidate data.

Example LLM input:

```json
{
  "user_request": "Necesito 5 kg de arroz y 2 litros de leche Gloria. Prioriza barato.",
  "preferences": {
    "price_priority": "high",
    "brand_priority": "medium",
    "allow_substitutions": true
  },
  "candidates": {
    "arroz": [
      {
        "store": "plaza_vea",
        "title": "Arroz Costeño 5 kg",
        "price": 24.90,
        "quantity_value": 5,
        "quantity_unit": "kg",
        "unit_price": 4.98,
        "required_units": 1,
        "total_price": 24.90,
        "product_url": "https://..."
      }
    ]
  }
}
```

Expected LLM output:

```json
{
  "cart": [
    {
      "requested_item": "arroz 5 kg",
      "selected_product": "Arroz Costeño 5 kg",
      "store": "plaza_vea",
      "required_units": 1,
      "estimated_total": 24.90,
      "reason": "Best balance between exact quantity and lowest total price.",
      "product_url": "https://..."
    }
  ],
  "total_estimated_cost": 24.90,
  "warnings": [],
  "questions": []
}
```

The LLM must explain the decision briefly, but the ranking must be supported by deterministic calculations.

---

## 6. Non-Functional Requirements

### NFR-001 — Maintainable Codebase

The project must use a clean and scalable structure.

Avoid:

- Random scripts in root.
- Duplicated scraper logic.
- Hardcoded selectors everywhere.
- Unused files.
- Mixed concerns.
- Large files with unrelated responsibilities.
- Raw LLM calls without schema validation.

---

### NFR-002 — Performance

The system must avoid unnecessary LLM usage.

Target:

```text
LLM calls:
1. Intent extraction.
2. Final cart reasoning.
```

Do not call the LLM for every product candidate.

---

### NFR-003 — Reliability

Scrapers must handle:

- No results.
- Timeout.
- Layout changes.
- Missing price.
- Missing product URL.
- Lazy-loaded results.
- Pagination or infinite scroll.
- Blocking or anti-bot friction.

For MVP, graceful degradation is acceptable:

```text
"If Metro fails, continue with Plaza Vea, Vivanda and Tottus."
```

---

### NFR-004 — Debuggability

Each scraping execution must save:

- Search query.
- Store.
- Timestamp.
- Raw HTML snapshot.
- Raw extracted JSON.
- Normalized JSON.
- Errors, if any.
- Screenshot when useful.

---

## 7. Proposed Tech Stack

### Frontend

Recommended:

```text
React + Vite + TypeScript
Tailwind CSS
shadcn/ui optional
```

Minimum UI modules:

```text
ChatPanel
PreferencesPanel
CartSummary
CandidateProductsTable
ProductCard
```

---

### Backend

Recommended:

```text
Python 3.11+
FastAPI
Pydantic
Playwright
SQLite or local JSON storage
```

Core backend responsibilities:

```text
API endpoints
Intent extraction
Scraping orchestration
Product normalization
Prefiltering
Ranking
LLM orchestration
Persistence
```

---

### LLM Provider

Support configurable provider:

```text
OpenAI API
Optional OpenCode-compatible provider if available
```

Use environment variables:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

Do not hardcode API keys.

---

### Storage

For MVP:

```text
SQLite preferred
Local JSON acceptable for preferences
```

Suggested:

```text
SQLite:
- scraped_products
- normalized_products
- cart_sessions
- user_preferences

JSON:
- temporary scraper outputs
- debug snapshots
```

---

## 8. Suggested Folder Structure

```text
ai-shopping-cart-assistant/
│
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes_chat.py
│   │   │   ├── routes_preferences.py
│   │   │   ├── routes_products.py
│   │   │   └── routes_cart.py
│   │   │
│   │   ├── models/
│   │   │   ├── intent_models.py
│   │   │   ├── product_models.py
│   │   │   ├── cart_models.py
│   │   │   └── preference_models.py
│   │   │
│   │   ├── services/
│   │   │   ├── intent_service.py
│   │   │   ├── scraping_service.py
│   │   │   ├── normalization_service.py
│   │   │   ├── filtering_service.py
│   │   │   ├── ranking_service.py
│   │   │   ├── cart_service.py
│   │   │   └── llm_service.py
│   │   │
│   │   ├── scrapers/
│   │   │   ├── base_scraper.py
│   │   │   ├── plaza_vea_scraper.py
│   │   │   ├── metro_scraper.py
│   │   │   ├── vivanda_scraper.py
│   │   │   └── tottus_scraper.py
│   │   │
│   │   ├── utils/
│   │   │   ├── text_cleaning.py
│   │   │   ├── unit_parser.py
│   │   │   ├── price_parser.py
│   │   │   ├── brand_parser.py
│   │   │   └── logging_utils.py
│   │   │
│   │   └── db/
│   │       ├── database.py
│   │       ├── repositories.py
│   │       └── migrations/
│   │
│   └── tests/
│       ├── test_unit_parser.py
│       ├── test_price_parser.py
│       ├── test_filtering.py
│       ├── test_ranking.py
│       └── test_intent_extraction.py
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── PreferencesPanel.tsx
│   │   │   ├── CartSummary.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   └── CandidateProductsTable.tsx
│   │   └── types/
│   │       ├── product.ts
│   │       ├── cart.ts
│   │       └── preferences.ts
│   │
│   └── public/
│
├── data/
│   ├── raw_html/
│   │   ├── plaza_vea/
│   │   ├── metro/
│   │   ├── vivanda/
│   │   └── tottus/
│   ├── screenshots/
│   ├── raw_json/
│   ├── normalized_json/
│   └── user_preferences.json
│
├── prompts/
│   ├── intent_extraction_prompt.md
│   └── cart_reasoning_prompt.md
│
└── docs/
    ├── architecture.md
    ├── scraping_notes.md
    ├── product_schema.md
    └── mvp_scope.md
```

---

## 9. API Design

### POST `/api/chat`

Input:

```json
{
  "message": "Necesito 5 kg de arroz y 2 litros de leche.",
  "session_id": "optional"
}
```

Output:

```json
{
  "intent": {},
  "cart": [],
  "candidate_products": {},
  "warnings": []
}
```

---

### GET `/api/preferences`

Returns user preferences.

---

### POST `/api/preferences`

Updates user preferences.

---

### POST `/api/products/search`

Input:

```json
{
  "query": "arroz",
  "stores": ["plaza_vea", "metro", "vivanda", "tottus"]
}
```

Output:

```json
{
  "products": []
}
```

---

## 10. Development Phases

## Phase 0 — Project Setup

### Goal

Create a clean base project with backend, frontend and clear folder structure.

### Tasks

- Create repository structure.
- Add `.env.example`.
- Configure backend with FastAPI.
- Configure frontend with React + Vite + TypeScript.
- Add basic logging.
- Add base Pydantic models.
- Add README with setup instructions.
- Add `.gitignore`.
- Add simple health check endpoint.

### Deliverables

```text
/backend running locally
/frontend running locally
/api/health working
Clean folder structure
README.md
```

### Definition of Done

- Project runs locally.
- No random files in root.
- Backend and frontend are separated.
- Environment variables are documented.

---

## Phase 1 — Data Models and Schemas

### Goal

Define stable schemas before scraping and LLM integration.

### Tasks

- Create `ProductCandidate` model.
- Create `ShoppingIntentItem` model.
- Create `UserPreferences` model.
- Create `CartItem` model.
- Create `CartRecommendation` model.
- Create schema validation tests.

### Deliverables

```text
backend/app/models/product_models.py
backend/app/models/intent_models.py
backend/app/models/preference_models.py
backend/app/models/cart_models.py
```

### Definition of Done

- All models validate sample JSON.
- Invalid product data fails clearly.
- Unit and price fields are typed correctly.

---

## Phase 2 — Unit, Price and Text Parsing

### Goal

Build deterministic parsing utilities before scraping at scale.

### Tasks

- Implement price parser.
- Implement unit parser.
- Implement quantity normalizer.
- Implement text cleaner.
- Implement brand extractor baseline.
- Implement tests.

### Examples to support

```text
"S/ 24.90" → 24.90
"Arroz 5 kg" → 5, "kg"
"Leche 900 ml" → 0.9, "l"
"Pack x 6" → 6, "unit"
"2x1" → flag as promotion, do not overprocess in MVP
```

### Definition of Done

- Parser tests pass.
- Unit normalization works for kg, g, l, ml, unit, pack.
- Ambiguous cases are flagged instead of silently guessed.

---

## Phase 3 — Intent Extraction

### Goal

Turn user messages into structured shopping intents.

### Tasks

- Create `intent_extraction_prompt.md`.
- Implement `IntentService`.
- Validate LLM output with Pydantic.
- Add fallback if LLM output is invalid.
- Add examples and tests.

### Prompt behavior

The LLM must extract structure only. It must not recommend products at this stage.

### Definition of Done

- Input message returns valid shopping intent JSON.
- Quantity, unit and brand are extracted when present.
- Missing values are represented as `null`, not hallucinated.
- Output is validated.

---

## Phase 4 — Scraper Base Architecture

### Goal

Create reusable scraper infrastructure.

### Tasks

- Implement `BaseScraper`.
- Define common scraper interface:

```python
async def search_products(self, query: str) -> list[ProductCandidate]:
    ...
```

- Add Playwright browser setup.
- Add HTML snapshot saving.
- Add screenshot saving.
- Add timeout and error handling.
- Add structured logging.

### Definition of Done

- A dummy scraper can return normalized product candidates.
- HTML and screenshot folders are created automatically.
- Errors are logged without crashing the whole pipeline.

---

## Phase 5 — Store Scrapers

### Goal

Implement store-specific scrapers.

### Stores

Priority order:

1. Plaza Vea.
2. Metro.
3. Tottus.
4. Vivanda.

### Tasks per store

- Use Playwright CLI workflow to inspect website.
- Search for a product.
- Save HTML.
- Take screenshot.
- Identify product card selectors.
- Extract:
  - title
  - price
  - presentation
  - product URL
  - image URL
  - availability if visible
- Normalize output to `ProductCandidate`.

### Important instruction

For each store, first implement a narrow proof of concept using one query:

```text
arroz
```

Then test:

```text
leche
detergente
papel higiénico
aceite
```

### Definition of Done

- Each store returns at least 10 product candidates for a common query when available.
- Product URLs are captured.
- Price is parsed.
- Title is parsed.
- Results are saved to raw and normalized JSON.

---

## Phase 6 — Pre-filtering Engine

### Goal

Reduce thousands of raw products into a compact candidate list.

### Tasks

- Implement product relevance scoring.
- Remove obviously irrelevant products.
- Penalize products with unrelated titles.
- Boost exact product keyword matches.
- Boost brand match if requested.
- Boost category/presentation match.
- Reject very low relevance scores.
- Return top N candidates per product per store or globally.

### Output

For each requested item:

```json
{
  "query": "arroz",
  "top_candidates": []
}
```

### Definition of Done

- For `"arroz"`, unrelated items are excluded.
- For `"leche gloria"`, Gloria products are prioritized.
- Candidate count is capped before LLM call.
- Filtering is deterministic and testable.

---

## Phase 7 — Ranking and Cart Builder

### Goal

Select the best product combination according to the user's preferences.

### Tasks

- Calculate required units.
- Calculate total price.
- Calculate unit price.
- Apply price, brand, store and quantity matching weights.
- Penalize excessive overbuying.
- Select best candidate per requested item.
- Return alternatives.

### Definition of Done

- User asking for 5 kg can receive 1 x 5 kg or 5 x 1 kg depending on total price and preference.
- Ranking explanation is transparent.
- Cart total is calculated.
- Alternative products are shown.

---

## Phase 8 — LLM Final Reasoning

### Goal

Use the LLM only after deterministic filtering/ranking.

### Tasks

- Create `cart_reasoning_prompt.md`.
- Send only top candidates.
- Ask LLM to produce short final recommendation.
- Validate response format.
- Avoid hallucinated products or prices.
- Preserve product URLs exactly.

### Definition of Done

- LLM does not invent products.
- LLM explains selected products using available candidate data.
- Final cart JSON is valid.
- Product links are preserved.

---

## Phase 9 — Web Interface

### Goal

Create a simple but attractive web UI.

### UI Requirements

- Chat input.
- Preferences panel.
- Cart summary.
- Candidate product cards/table.
- Loading state.
- Error messages.
- Links to open product pages.
- Minimal clean design.

### Suggested layout

```text
Left:
- User preferences
- Store selection

Center:
- Chat conversation

Right:
- Recommended cart
- Alternatives
- Total cost
```

### Definition of Done

- User can send request from UI.
- UI displays recommended cart.
- UI displays product links.
- User can adjust preferences.
- UI is visually clean and demo-ready.

---

## Phase 10 — Demo Scenario

### Goal

Prepare one polished MVP demo.

### Demo input

```text
Necesito 5 kg de arroz, 2 litros de leche Gloria, papel higiénico barato y detergente. Prioriza precio bajo, pero evita marcas demasiado desconocidas.
```

### Expected demo output

- Structured intent shown internally or optionally in debug mode.
- Scraping status per store.
- Candidate list.
- Recommended cart.
- Alternatives.
- Estimated total.
- Product links.

### Demo Success Criteria

The demo is successful if:

- The assistant understands the request.
- Scrapers return real products.
- Irrelevant products are filtered.
- The cart recommendation is reasonable.
- Links open the selected product pages.
- The UI is understandable without explanation.

---

## 11. Agent Instructions

Use the following instructions when delegating this project to an AI coding agent.

---

# Master Prompt for AI Coding Agent

You are a senior full-stack engineer and AI systems architect. Build an MVP called **AI Shopping Cart Assistant**.

The product is a conversational web app that helps a user build a supermarket shopping cart from natural language.

The user writes something like:

```text
"Necesito 5 kg de arroz, 2 litros de leche Gloria, papel higiénico barato y detergente. Prioriza precios bajos pero evita marcas desconocidas."
```

The app must:

1. Extract structured shopping intent from natural language.
2. Search products across Plaza Vea, Metro, Vivanda and Tottus.
3. Scrape product search results using Playwright CLI-oriented workflows.
4. Normalize scraped results into a standard JSON schema.
5. Pre-filter irrelevant results before using any LLM.
6. Rank candidates using deterministic scoring.
7. Use the LLM only for intent extraction and final cart explanation.
8. Recommend a cart with product URLs and estimated total price.
9. Show results in a clean web interface.

Important architecture rule:

Do not send raw scraped dumps to the LLM. The LLM must only receive top filtered candidates.

Use this stack unless there is a strong reason not to:

```text
Frontend:
- React
- Vite
- TypeScript
- Tailwind CSS

Backend:
- Python 3.11+
- FastAPI
- Pydantic
- Playwright
- SQLite or local JSON storage

LLM:
- OpenAI API by default
- Provider should be configurable through environment variables
```

You must create a clean project structure. Avoid random scripts and unorganized files. Follow the folder structure defined in this document.

Use Playwright through CLI-oriented development practices:

- Inspect target pages.
- Save HTML snapshots.
- Take screenshots.
- Use robust locators.
- Avoid brittle selectors when possible.
- Keep one scraper per store.
- Save raw and normalized scraping outputs.

Build the project in phases:

1. Project setup.
2. Data models.
3. Unit, price and text parsing.
4. Intent extraction.
5. Scraper base architecture.
6. Store scrapers.
7. Pre-filtering engine.
8. Ranking and cart builder.
9. LLM final reasoning.
10. Web interface.
11. Demo scenario.

Prioritize working MVP over excessive polish.

Do not implement:

- Checkout automation.
- Payment.
- Production login.
- Coupon optimization.
- Full catalog crawling.
- Multi-user accounts.
- Browser extension.
- Mobile app.

The MVP must be demo-ready, not production-perfect.

At each implementation step:

- Keep files organized.
- Add minimal tests for parsers, filtering and ranking.
- Validate all LLM outputs with Pydantic.
- Preserve product links exactly.
- Log scraper failures without crashing the whole system.
- Add clear README instructions.

Start by creating the repository structure, backend health endpoint, frontend base UI and shared schemas. Then continue phase by phase.

---

## 12. Technical Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Store websites change layout | High | Isolate one scraper per store and save HTML snapshots |
| Too many products for LLM | High | Deterministic pre-filtering and top-N candidate cap |
| Search results are irrelevant | High | Relevance scoring, negative keywords and category/title matching |
| Unit parsing errors | Medium | Dedicated parser tests and confidence flags |
| Anti-bot friction | Medium | Graceful degradation and per-store failures |
| Product availability changes | Medium | Show warning that prices and availability are estimated |
| Login automation becomes unstable | High | Keep login out of MVP |
| UI consumes too much time | Medium | Use simple layout and reusable components |
| LLM hallucinates products | High | Validate output and restrict it to provided candidates |

---

## 13. MVP Priorities

### Must Have

- Natural language input.
- Structured intent extraction.
- At least 2 working store scrapers.
- Normalized product JSON.
- Product URLs.
- Pre-filtering.
- Ranking.
- Cart recommendation.
- Basic UI.

### Should Have

- 4 working store scrapers.
- User preference memory.
- Alternatives per product.
- Screenshots and HTML snapshots.
- SQLite persistence.

### Could Have

- Store selector.
- Debug mode.
- Cart export to JSON.
- Manual link opening workflow.
- Better UI polish.

### Not Needed Now

- Checkout automation.
- Auto-login.
- Payment.
- Full user accounts.
- Advanced recommendation learning.

---

## 14. Acceptance Criteria

The MVP is accepted when:

1. A user can enter a shopping request in natural language.
2. The backend extracts structured shopping intent.
3. The system searches at least 2 supermarket websites.
4. Scraped products are normalized into a consistent schema.
5. Irrelevant products are filtered before LLM usage.
6. The system recommends a reasonable cart.
7. The recommendation includes prices, quantities, stores and links.
8. The UI displays the result clearly.
9. The codebase is organized and understandable.
10. The demo scenario runs end-to-end.

---

## 15. Final Implementation Guidance

Build the system as a pipeline, not as a single giant agent.

Correct architecture:

```text
User Input
  → Intent Extraction
  → Search Query Planning
  → Scraping
  → Normalization
  → Filtering
  → Ranking
  → LLM Explanation
  → UI Cart Display
```

Wrong architecture:

```text
User Input
  → Scrape everything
  → Send all JSON to LLM
  → Hope the model decides correctly
```

The MVP must be practical, deterministic where possible, and easy to debug.
