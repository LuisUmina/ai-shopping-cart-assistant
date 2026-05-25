from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper
from app.utils.brand_parser import extract_brand
from app.utils.price_parser import parse_price
from app.utils.unit_parser import parse_quantity

_BASE_URL = "https://www.metro.pe"
# Navigate directly to search results — avoids the race condition where
# homepage carousels already contain article[data-cnstrc-item-id] and
# wait_for_selector() resolves before the page actually navigates.
_SEARCH_URL = _BASE_URL + "/s?q={query}&sort=score_desc"

# Primary: VTEX product summary elements (Metro's current structure).
# Fallback: Constructor.io data attributes (older Metro structure).
_PRODUCT_SELECTOR = "[class*='vtex-product-summary-2-x-element'], article[data-cnstrc-item-id]"

_EXTRACT_JS = """() => {
    // Try constructor.io attributes first (previous Metro structure)
    const cnstrc = document.querySelectorAll('article[data-cnstrc-item-id]');
    if (cnstrc.length > 0) {
        return Array.from(cnstrc).map(article => {
            const linkEl = article.closest('a') || article.parentElement?.closest('a');
            const imgEl  = article.querySelector('img');
            return {
                product_id: article.getAttribute('data-cnstrc-item-id') || '',
                title:      article.getAttribute('data-cnstrc-item-name') || '',
                price:      article.getAttribute('data-cnstrc-item-price') || '',
                link:       linkEl ? (linkEl.getAttribute('href') || '') : '',
                image:      imgEl  ? (imgEl.getAttribute('src')  || '') : '',
            };
        });
    }
    // VTEX product summary fallback (current Metro structure)
    const els = document.querySelectorAll("[class*='vtex-product-summary-2-x-element']");
    return Array.from(els).map(el => {
        const linkEl  = el.querySelector('a[href]');
        const imgEl   = el.querySelector('img');
        const nameEl  = el.querySelector("[class*='productBrand']")
                     || el.querySelector("[class*='productName']");
        const priceEl = el.querySelector("[class*='sellingPriceValue']")
                     || el.querySelector("[class*='currencyContainer']");
        const skuEl   = el.querySelector('[data-sku]') || el.querySelector('[data-product-id]');
        return {
            product_id: skuEl ? (skuEl.getAttribute('data-sku') || skuEl.getAttribute('data-product-id') || '') : '',
            title:      nameEl  ? nameEl.textContent.trim()                         : '',
            price:      priceEl ? priceEl.textContent.replace(/[^0-9.,]/g, '').trim() : '',
            link:       linkEl  ? linkEl.href                                        : '',
            image:      imgEl   ? (imgEl.getAttribute('src') || imgEl.getAttribute('data-src') || '') : '',
        };
    });
}"""


class MetroScraper(BaseScraper):
    def __init__(
        self,
        data_dir: Path,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        super().__init__(
            store_id=StoreId.METRO,
            data_dir=data_dir,
            headless=headless,
            timeout_ms=timeout_ms,
        )

    async def search_products(self, query: str) -> list[ProductCandidate]:
        try:
            return await self._do_search(query)
        except Exception as exc:
            self.logger.error("search_products failed for %r: %s", query, exc)
            return []

    async def _do_search(self, query: str) -> list[ProductCandidate]:
        search_url = _SEARCH_URL.format(query=quote(query))
        page = await self._new_page()
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            await page.wait_for_timeout(3_000)
            await self._dismiss_popups(page)
            await page.wait_for_selector(_PRODUCT_SELECTOR, timeout=15_000)
            await page.wait_for_timeout(2_000)

            self.logger.info("Metro results URL: %s", page.url)
            self.save_html(await page.content(), query)

            raw_items: list[dict] = await page.evaluate(_EXTRACT_JS)
            self.save_raw_json(raw_items, query)
            return [self._to_candidate(item, query) for item in raw_items if item.get("title")]
        finally:
            await page.close()

    def _to_candidate(self, item: dict, query: str) -> ProductCandidate:
        parsed_price = parse_price(item.get("price", ""))
        price_val = parsed_price.value if (parsed_price and parsed_price.value is not None) else 0.0

        title = item.get("title", "")
        parsed_brand = extract_brand(title)
        brand = parsed_brand.brand if parsed_brand.confidence >= 0.9 else None
        parsed_qty = parse_quantity(title)
        qty_value = parsed_qty.value if (parsed_qty and parsed_qty.value) else 1.0
        qty_unit = parsed_qty.unit if (parsed_qty and parsed_qty.unit) else QuantityUnit.UNIT
        unit_price = round(price_val / qty_value, 4) if qty_value else price_val

        link = item.get("link", "")
        if link and not link.startswith("http"):
            link = _BASE_URL + link

        return ProductCandidate(
            store=StoreId.METRO,
            product_id=item.get("product_id") or None,
            title=title,
            brand=brand,
            raw_price=item.get("price") or None,
            price=price_val,
            presentation_text=title,
            quantity_value=qty_value,
            quantity_unit=qty_unit,
            unit_price=unit_price,
            unit_price_unit=qty_unit,
            availability=Availability.AVAILABLE,
            image_url=item.get("image") or None,
            product_url=link,
            search_query=query,
            scraped_at=datetime.now(timezone.utc),
        )
