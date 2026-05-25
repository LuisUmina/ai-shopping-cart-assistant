# AI Shopping Cart Assistant

Aplicacion web conversacional para construir un carrito de compras de supermercados peruanos a partir de lenguaje natural. El usuario escribe un pedido como `Necesito 5 kg de arroz, 2 litros de leche Gloria y papel higienico barato`, el sistema extrae intencion estructurada, busca productos reales en supermercados, filtra resultados irrelevantes, rankea candidatos con reglas deterministicas y propone un carrito final con alternativas.

El LLM no decide libremente productos ni precios. En esta arquitectura el LLM se usa para dos tareas acotadas: extraer la intencion de compra y redactar/validar explicaciones finales sobre productos ya seleccionados por el pipeline deterministico.

## Objetivo Del Proyecto

El objetivo es construir un asistente de compra tipo MVP que ayude al usuario a:

- Convertir una frase natural en una lista estructurada de productos.
- Buscar productos reales en Plaza Vea, Metro, Vivanda y Tottus.
- Comparar opciones por precio unitario, marca, cantidad, presentacion, relevancia y tienda.
- Generar un carrito recomendado con enlaces a los productos.
- Mostrar alternativas y un panel de debug para entender por que gano cada producto.
- Mantener preferencias de compra reutilizables entre busquedas.

No es un sistema de checkout automatico. El MVP no realiza pagos, no confirma pedidos y no automatiza compras. La compra automatica esta marcada como funcionalidad futura en la interfaz.

## Stack Tecnico

Backend:
- Python 3.11+
- FastAPI
- Pydantic v2
- Pydantic Settings
- Playwright
- OpenAI SDK compatible con OpenAI y endpoints OpenAI-compatible
- Pytest y pytest-asyncio para pruebas

Frontend:
- React 19
- TypeScript 6
- Vite 8
- Tailwind CSS v4
- Web Speech API para dictado por voz cuando el navegador lo soporta

LLM:
- OpenAI por defecto
- OpenCode u otro endpoint compatible con OpenAI mediante variables de entorno

## Estructura Del Proyecto

```text
.
├── backend/
│   ├── app/
│   │   ├── api/                 # Rutas FastAPI
│   │   ├── models/              # Modelos Pydantic
│   │   ├── scrapers/            # Scrapers Playwright por tienda
│   │   ├── services/            # Logica de pipeline, ranking, carrito, LLM
│   │   ├── utils/               # Parsers y utilidades
│   │   ├── config.py            # Configuracion por .env
│   │   ├── dependencies.py      # Inyeccion de dependencias FastAPI
│   │   └── main.py              # App FastAPI
│   ├── tests/                   # Pruebas unitarias/backend
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/                 # Cliente HTTP del frontend
│   │   ├── components/          # Componentes React
│   │   ├── types/               # Tipos TypeScript compartidos
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── prompts/
│   ├── intent_extraction_prompt.md
│   └── cart_reasoning_prompt.md
├── data/
│   ├── user_preferences.json    # Preferencias persistidas
│   ├── raw_html/                # Artefactos de scraping
│   ├── raw_json/                # Extracciones crudas por tienda
│   └── screenshots/             # Capturas de debug
├── .env.example
├── README.md
└── ai_shopping_cart_assistant_mvp_plan.md
```

## Flujo End-To-End

```text
Usuario escribe en el chat
        ↓
POST /api/chat
        ↓
IntentService extrae ShoppingIntent con LLM
        ↓
Se cargan preferencias desde data/user_preferences.json
        ↓
ScrapingService busca cada producto en tiendas preferidas
        ↓
FilteringService elimina candidatos irrelevantes
        ↓
RankingService ordena candidatos con scoring ponderado
        ↓
CartBuilder selecciona el top 1 y calcula unidades/totales
        ↓
CartReasoningService agrega explicaciones y puede pedir swaps seguros
        ↓
Frontend muestra carrito, alternativas y debug del pipeline
```

## Backend

### API Principal

Rutas principales:

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/api/health` | Estado del backend y proveedor LLM activo |
| `POST` | `/api/chat` | Ejecuta el pipeline completo de compra |
| `GET` | `/api/preferences` | Lee preferencias persistidas |
| `POST` | `/api/preferences` | Guarda preferencias persistidas |

### `POST /api/chat`

Request:

```json
{
  "message": "Necesito 5 kg de arroz, 2 litros de leche Gloria y papel higienico barato",
  "session_id": null
}
```

Response resumida:

```json
{
  "intent": {
    "shopping_intent": [
      {
        "raw_text": "5 kg de arroz",
        "product_query": "arroz",
        "quantity": 5,
        "unit": "kg",
        "brand_preference": null,
        "price_sensitivity": "medium",
        "allow_substitution": true
      }
    ]
  },
  "cart": {
    "cart": [],
    "total_estimated_cost": 0,
    "warnings": [],
    "questions": []
  },
  "candidate_products": {},
  "warnings": [],
  "pipeline_debug": null
}
```

## Modelos De Dominio

### `ShoppingIntentItem`

Representa un producto pedido por el usuario.

Campos principales:

| Campo | Tipo | Significado |
|---|---|---|
| `raw_text` | `str` | Fragmento original del usuario |
| `product_query` | `str` | Keyword simplificada para buscar |
| `quantity` | `float \| null` | Cantidad requerida |
| `unit` | `QuantityUnit \| null` | Unidad requerida |
| `brand_preference` | `str \| null` | Marca mencionada por el usuario |
| `price_sensitivity` | `Priority` | Sensibilidad al precio extraida del texto |
| `allow_substitution` | `bool` | Si el usuario permite sustitucion para ese item |

### `ProductCandidate`

Representa un producto normalizado desde una tienda.

Campos principales:

| Campo | Significado |
|---|---|
| `store` | Tienda de origen |
| `product_id` | ID/SKU cuando existe |
| `title` | Nombre del producto |
| `brand` | Marca detectada o extraida |
| `category` | Categoria cuando la tienda la expone |
| `price` | Precio total de la presentacion |
| `quantity_value` | Cantidad contenida en la presentacion |
| `quantity_unit` | Unidad de la presentacion |
| `unit_price` | Precio normalizado por unidad |
| `availability` | `available`, `unavailable` o `unknown` |
| `product_url` | URL para abrir el producto |
| `search_query` | Query que produjo el candidato |
| `scraped_at` | Fecha/hora de scraping |

### `UserPreferences`

Preferencias persistidas en `data/user_preferences.json`.

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

Estado actual de uso:

| Preferencia | Estado | Uso real |
|---|---|---|
| `price_priority` | Activa | Ajusta el peso del precio en ranking |
| `brand_priority` | Activa | Ajusta el peso de marca en ranking |
| `known_brands_only` | Activa parcial | Penaliza productos sin marca detectada |
| `preferred_stores` | Activa | Define que tiendas se scrapean |
| `excluded_brands` | Activa backend | Excluye marcas si la marca fue detectada |
| `preferred_brands` | Activa backend | Da bonus a marcas preferidas si existen |
| `max_candidates_per_product` | Activa | Limita candidatos que pasan a ranking |
| `allow_substitutions` | Preparada | Existe en preferencias, pero la sustitucion efectiva depende principalmente del intent por item |
| `allow_equivalent_sizes` | Preparada | Existe en modelo, pero no controla aun el calculo de equivalencias |

## Scraping

El scraping usa Playwright con Chromium headless. `ScrapingService` ejecuta tiendas en paralelo y mantiene las queries secuenciales dentro de cada tienda para controlar memoria y estabilidad.

### Estrategia Por Tienda

| Tienda | Metodo de acceso | Metodo de extraccion | Metadata fuerte |
|---|---|---|---|
| Plaza Vea | Home + buscador simulado | Atributos HTML `data-ga-*` | Titulo, marca, categoria, precio, stock |
| Metro | Home + buscador simulado | Selectores VTEX | Titulo, precio, link; marca inferida |
| Vivanda | URL directa `/search/{query}` | JSON-LD `ItemList` | Titulo, marca, precio, disponibilidad |
| Tottus | Home + buscador simulado | `__NEXT_DATA__` de Next.js | Titulo, marca, precio, formato |

### Paralelismo

```text
ScrapingService.search(queries, stores)
        ↓
asyncio.gather por tienda
        ↓
un navegador Playwright por tienda
        ↓
queries secuenciales dentro de cada navegador
        ↓
merge por query: { "arroz": [candidatos de todas las tiendas] }
```

En Windows se crea un event loop dedicado por tienda en un thread separado porque Playwright necesita `ProactorEventLoop` para lanzar procesos de navegador correctamente.

### Artefactos De Debug

Cada scraper puede guardar:

```text
data/raw_html/{store}/...
data/raw_json/{store}/...
data/screenshots/{store}/...
```

Estos artefactos ayudan a diagnosticar cambios de estructura en paginas de supermercados.

## Reglas De Negocio

El sistema tiene dos etapas principales antes de construir el carrito: filtrado y ranking.

### 1. Filtrado Deterministico

Archivo: `backend/app/services/filtering_service.py`

El filtrado elimina candidatos irrelevantes antes del ranking. Cada candidato recibe un score de relevancia entre `0.0` y `1.0`.

Reglas duras:

- Si la marca esta en `excluded_brands`, el candidato se descarta.
- Si `availability == unavailable`, el candidato se descarta.
- Si el score final es menor a `0.55`, el candidato se descarta.
- Solo pasan los primeros `max_candidates_per_product` candidatos despues de ordenar por score de filtro.

Formula actual:

```text
filter_score =
    title_score    * 0.65
  + category_score * 0.10
  + brand_score    * 0.15
  + unit_score     * 0.10
  - negative_keyword_penalty
```

Penalizacion por palabras negativas:

```text
negative_keyword_penalty = 0.50 si el titulo contiene alguna palabra negativa
```

Palabras negativas actuales:

```text
taper, tapers, olla, ollas, receta, recetario, libro, libros, copa, copas,
funda, fundas, accesorio, accesorios, utensilio, utensilios, molde, moldes,
bandeja, bandejas, dispensador, sticker, horno, soporte, gancho, colgador
```

#### `title_score`

```text
title_score = tokens_del_query_en_titulo / total_tokens_query
```

Ejemplo:

```text
query: "papel higienico"
titulo: "Papel Higienico Elite Doble Hoja"
tokens encontrados: papel, higienico
score = 2 / 2 = 1.0
```

#### `category_score`

```text
1.0 si algun token del query aparece en la categoria
0.5 si la categoria no existe
0.0 si existe categoria pero no coincide
```

El valor `0.5` para categoria desconocida evita castigar tiendas que no exponen categoria estructurada.

#### `brand_score` En Filtrado

```text
Si el usuario pidio una marca y coincide: 1.0
Si pidio marca, no coincide y permite sustitucion: 0.3
Si pidio marca, no coincide y no permite sustitucion: 0.0
Si hay preferred_brands y la marca esta ahi: 1.0
Si known_brands_only=true y no hay marca detectada: 0.0
Sin preferencia de marca: 0.5
```

#### `unit_score`

```text
1.0 si las unidades son compatibles
0.5 si el usuario no pidio unidad especifica
0.0 si las unidades son incompatibles
```

Compatibilidades:

```text
masa:   g, kg
volumen: ml, l
conteo: unit, pack, roll, bag, box
```

### 2. Ranking Deterministico

Archivo: `backend/app/services/ranking_service.py`

El ranking ordena candidatos ya filtrados. El primer candidato del ranking es el producto seleccionado para el carrito.

Formula conceptual:

```text
final_score =
    relevance_score  * w_relevance
  + price_score      * w_price
  + unit_match_score * w_unit
  + brand_score      * w_brand
  + store_score      * w_store
```

Pesos base antes de normalizar:

```text
relevance = 0.35
price     = 0.25 * priority_factor(effective_price_priority)
unit      = 0.15
brand     = 0.15 * priority_factor(brand_priority)
store     = 0.10
```

Factores de prioridad:

```text
high   = 1.5
medium = 1.0
low    = 0.5
```

Los pesos se normalizan para que la suma final sea `1.0`.

#### Precio Efectivo

El precio efectivo usa la mayor prioridad entre:

- `intent_item.price_sensitivity`, extraido del texto del usuario.
- `preferences.price_priority`, configurado en el panel izquierdo.

```text
effective_price_priority = max(intent_price_sensitivity, global_price_priority)
```

Esto significa que si el panel tiene precio alto, el sistema seguira dando importancia fuerte al precio aunque el texto del usuario no lo mencione.

#### `relevance_score`

```text
relevance_score = title_match * 0.90 + category_bonus
category_bonus maximo = 0.10
```

La categoria pesa poco para evitar sesgo a favor de Plaza Vea, porque Plaza Vea expone `data-ga-category` de forma mas consistente que otras tiendas.

#### `price_score`

El precio se compara usando `unit_price` entre candidatos pares.

```text
price_score = 1.0 - (candidate_unit_price - min_unit_price) / (max_unit_price - min_unit_price)
```

Interpretacion:

```text
producto mas barato = 1.0
producto mas caro   = 0.0
precios iguales     = 1.0 para todos
```

Ejemplo:

```text
Tottus    arroz unit_price 3.50 -> price_score 1.0
Metro     arroz unit_price 3.70 -> price_score 0.5
Vivanda   arroz unit_price 3.90 -> price_score 0.0
```

#### `unit_match_score`

Penaliza sobrecompra excesiva cuando el usuario pidio cantidad y unidad.

```text
sin cantidad requerida             -> 0.5
presentacion exacta o poco exceso  -> cercano a 1.0
comprar el doble de lo requerido   -> 0.5
exceso >= 2x lo requerido          -> 0.0
```

Formula:

```text
unit_match_score = max(0.0, 1.0 - excess_ratio * 0.5)
```

#### `brand_score` En Ranking

```text
marca pedida y coincide: 1.0
marca pedida no coincide, sustitucion permitida: 0.3
marca pedida no coincide, sustitucion no permitida: 0.0
marca en preferred_brands: 1.0
known_brands_only=true y sin marca: 0.0
sin preferencia: 0.5
```

#### `store_score`

```text
1.0 si la tienda esta en preferred_stores
0.0 si no esta
```

Como actualmente solo se scrapean tiendas preferidas, este score normalmente no diferencia mucho entre candidatos. Su valor es mas util si en el futuro se permite rankear candidatos de tiendas fuera de preferencias.

### 3. Construccion Del Carrito

Archivo: `backend/app/services/cart_builder.py`

Reglas:

- Para cada producto pedido, se toma el primer candidato del ranking.
- Los candidatos restantes se devuelven como alternativas.
- Si no hay candidatos, se agrega una advertencia.
- El total estimado es la suma de `required_units * selected.price`.

Calculo de unidades requeridas:

```text
required_units = ceil(cantidad_requerida_base / cantidad_producto_base)
effective_quantity = required_units * cantidad_producto_base
excess_quantity = effective_quantity - cantidad_requerida_base
```

Advertencia de sobrecompra:

```text
si excess_quantity / requested_quantity > 0.5 -> warning
```

Ejemplo:

```text
Usuario pide: 1 litro de leche
Producto: botella de 900 ml
required_units = ceil(1000 / 900) = 2
effective_quantity = 1800 ml
excess_quantity = 800 ml
exceso = 80%, se genera advertencia
```

### 4. Razonamiento Final Con LLM

Archivo: `backend/app/services/cart_reasoning_service.py`

El LLM recibe un resumen compacto del carrito ya construido y puede:

- Agregar razones por producto.
- Agregar preguntas de aclaracion.
- Agregar advertencias nuevas.
- Solicitar un swap a una alternativa existente si detecta un error claro.

El LLM no puede inventar productos, precios ni tiendas. Solo puede elegir entre alternativas que ya pasaron filtrado y ranking.

Reglas de swap:

- Solo si hay error claro de categoria, variante o producto completamente distinto.
- Solo puede usar indices existentes en `alternatives`.
- Si el producto es razonable, no debe cambiarlo.

## Preferencias: Panel Izquierdo Vs Chat

El panel izquierdo representa preferencias generales persistidas. El chat representa instrucciones especificas de la busqueda actual.

Ejemplos:

```text
Panel: Precio alta
Chat: "papel higienico barato"
Resultado: el precio tiene mucha importancia.
```

```text
Panel: Marca media
Chat: "leche Gloria"
Resultado: el intent incluye marca Gloria y el ranking favorece coincidencias de marca.
```

Importante: la logica actual usa la mayor prioridad de precio entre panel y chat. Por eso, si el panel dice precio alto, la busqueda seguira favoreciendo precio aunque el usuario no escriba "barato".

## Frontend

La interfaz esta organizada en tres columnas en escritorio:

```text
Preferencias | Chat | Carrito recomendado
```

En mobile se usa navegacion inferior con tres tabs:

```text
Preferencias | Chat | Carrito
```

### Componentes Principales

| Componente | Responsabilidad |
|---|---|
| `App.tsx` | Layout general y estado de carrito activo |
| `PreferencesPanel.tsx` | Preferencias, tiendas, prioridades y autoguardado |
| `ChatPanel.tsx` | Chat, dictado, loading steps, mensajes y debug |
| `CandidateProductsTable.tsx` | Acordeon de candidatos evaluados por query |
| `DebugPanel.tsx` | Panel lateral con scores detallados |
| `CartSummary.tsx` | Tercera columna con carrito y CTA |
| `ProductCard.tsx` | Producto seleccionado y alternativas |
| `CheckoutPanel.tsx` | Resumen de compra y estado de compra automatica futura |

### Autoguardado De Preferencias

El panel de preferencias guarda automaticamente con debounce de 500 ms cuando el usuario cambia:

- Tiendas activas.
- Prioridad de precio.
- Prioridad de marca.
- Marcas conocidas.
- Cantidad de opciones evaluadas.

El indicador inferior muestra:

```text
Guardando preferencias...
Preferencias autoguardadas
No se pudo guardar
```

El backend sigue leyendo preferencias desde `data/user_preferences.json` cuando llega una nueva busqueda.

### Scroll Y Layout

Las tres columnas usan contenedores con alto completo, `min-h-0` y scroll interno para evitar que listas largas tapen el input o los botones.

Zonas con scroll:

- Columna de preferencias.
- Area de mensajes del chat.
- Lista de candidatos desplegados.
- Columna de carrito.
- Lista de alternativas dentro de cada producto.
- Panel de debug.
- Panel de checkout.

## Configuracion

Crear `.env` desde `.env.example`.

```bash
cp .env.example .env
```

Variables disponibles:

```env
APP_NAME=AI Shopping Cart Assistant
ENVIRONMENT=development

LLM_PROVIDER=openai

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini

OPENCODE_API_KEY=
OPENCODE_BASE_URL=
OPENCODE_MODEL=

SCRAPER_HEADLESS=true
SCRAPER_TIMEOUT_MS=30000
```

### Proveedor LLM

Usar OpenAI:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

Usar OpenCode u otro endpoint compatible:

```env
LLM_PROVIDER=opencode
OPENCODE_API_KEY=...
OPENCODE_BASE_URL=https://...
OPENCODE_MODEL=...
```

## Instalacion Y Ejecucion

### Backend En Windows PowerShell

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m playwright install chromium
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/api/health
```

### Backend En macOS/Linux

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

### Build Frontend

```bash
cd frontend
npm run build
```

### Preview Frontend

```bash
cd frontend
npm run preview
```

## Pruebas

Ejecutar backend tests:

```powershell
cd backend
.venv\Scripts\python.exe -m pytest tests/ -v
```

En macOS/Linux:

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
```

Areas cubiertas por tests:

- Modelos Pydantic.
- Parser de precios.
- Parser de unidades.
- Limpieza de texto.
- Extraccion de marca.
- Extraccion de intent.
- Base scraper.
- Store scrapers.
- FilteringService.
- RankingService.
- CartBuilder.
- CartReasoningService.
- ScrapingService.

## Debug Del Pipeline

Cada respuesta de chat incluye `pipeline_debug`, que alimenta el panel `Ver analisis detallado`.

Por cada query muestra:

- Total scrapeado.
- Conteo por tienda.
- Candidatos que pasaron filtro.
- Score de filtro por candidato.
- Score de ranking por candidato.

Componentes de filtro mostrados:

```text
Titulo
Marca
Categoria
Unidad
Score total
```

Componentes de ranking mostrados:

```text
Relevancia
Precio
Unidad
Marca
Tienda
Score final
```

## Consideraciones Sobre Plaza Vea Y Sesgos

Plaza Vea suele exponer mas metadata estructurada que otras tiendas:

- `data-ga-name`
- `data-ga-brand`
- `data-ga-category`
- `data-ga-price`
- `data-stock`

Esto puede darle ventaja en marca/categoria si otros scrapers no consiguen la misma informacion. Para reducir sesgo:

- La categoria pesa solo `0.10` en filtrado.
- En ranking la categoria solo agrega un bonus maximo de `0.10` dentro de relevancia.
- La disponibilidad no se usa como score de ranking porque no todas las tiendas reportan stock confiable.
- Productos `UNAVAILABLE` se eliminan antes de ranking.

Si aun asi Plaza Vea gana frecuentemente, revisar:

- Si otras tiendas estan activas en preferencias.
- Si los scrapers de otras tiendas estan devolviendo productos.
- Si los precios parseados son validos.
- Si Plaza Vea tiene mejor match de titulo o marca.
- El panel de debug para comparar `rank_price`, `rank_brand`, `rank_relevance` y `rank_final`.

## Limitaciones Actuales

- No hay checkout automatico real.
- No hay garantia de stock en tiempo real.
- No hay historial de precios.
- No hay optimizacion por cupones.
- No hay login multiusuario.
- No hay persistencia por usuario; las preferencias son un JSON local compartido.
- El scraping depende de estructuras de sitios externos que pueden cambiar.
- `allow_substitutions` global esta preparado, pero la sustitucion efectiva depende del intent por item.
- `allow_equivalent_sizes` esta preparado, pero todavia no gobierna la logica de equivalencias.
- El precio `0.0` puede aparecer si un scraper no logra parsear precio; conviene monitorearlo desde debug.
- El carrito es mixto por item; no optimiza por comprar todo en una sola tienda.

## Troubleshooting

### El backend no inicia

Revisar:

- Python 3.11+.
- `.env` existente en la raiz del repo.
- Dependencias instaladas con `pip install -e ".[dev]"`.
- API key configurada para el proveedor LLM activo.

### Playwright falla o no abre navegador

Ejecutar:

```bash
cd backend
python -m playwright install chromium
```

En Windows, el proyecto ya maneja event loops dedicados por tienda dentro de `ScrapingService`.

### No aparecen productos

Revisar:

- Que haya tiendas activas en preferencias.
- Que el backend tenga acceso a internet.
- Que los selectores de la tienda no hayan cambiado.
- Artefactos en `data/raw_html`, `data/raw_json` y `data/screenshots`.
- Logs del backend.

### Cambie preferencias pero no afectan la busqueda

El frontend usa autoguardado. Esperar a ver el estado `Preferencias autoguardadas` antes de lanzar una busqueda nueva.

El backend lee preferencias desde:

```text
data/user_preferences.json
```

### No veo el boton de compra

El boton de la tercera columna aparece siempre:

- Sin carrito: aparece deshabilitado con texto de compra pendiente.
- Con carrito: aparece activo como `Finalizar Compra`.

La compra automatica dentro del checkout sigue deshabilitada porque no forma parte del MVP.

### El chat o columnas no permiten llegar al final

La UI usa scroll interno en las tres columnas. Si el problema persiste:

- Refrescar el frontend dev server.
- Verificar que el build cargado sea el mas reciente.
- Revisar zoom del navegador.

## Comandos Rapidos

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

Tests backend:

```bash
cd backend
python -m pytest tests/ -v
```

Build frontend:

```bash
cd frontend
npm run build
```

## Estado Del MVP

Completado:

- Setup FastAPI y React/Vite.
- Modelos Pydantic.
- Parsers deterministicos de precio/unidad/texto/marca.
- Extraccion de intent con LLM.
- Scrapers Playwright para Plaza Vea, Metro, Vivanda y Tottus.
- Filtrado deterministico.
- Ranking deterministico.
- Construccion de carrito.
- Razonamiento final con LLM acotado.
- Interfaz web con preferencias, chat, carrito, checkout futuro y debug.
- Autoguardado de preferencias.
- Scroll interno en columnas y listas largas.

Pendiente o futuro:

- Compra automatica real.
- Mejor integracion de `allow_substitutions` global.
- Uso real de `allow_equivalent_sizes` como constraint configurable.
- Preferencias visuales para `preferred_brands` y `excluded_brands`.
- Optimizar carrito por una sola tienda cuando el usuario lo pida.
- Mejor manejo de precios invalidos o `0.0`.
- Mayor robustez ante cambios de HTML en supermercados.
