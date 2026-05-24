from datetime import datetime, timezone
from pathlib import Path

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper
from app.utils.price_parser import parse_price
from app.utils.unit_parser import parse_quantity

_BASE_URL = "https://www.metro.pe"
_SEARCH_SELECTORS = (
    "input[placeholder*='Busca']",
    "input[placeholder*='busca']",
    "input[type='search']",
    "input[class*='searchInput']",
    "header input",
)
_PRODUCT_SELECTOR = "article[data-cnstrc-item-id]"


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
        page = await self._new_page()
        try:
            await page.goto(_BASE_URL, wait_until="domcontentloaded", timeout=self.timeout_ms)
            await page.wait_for_timeout(2_000)
            await self._dismiss_popups(page)
            await self._submit_search(page, query, _SEARCH_SELECTORS)
            await page.wait_for_selector(_PRODUCT_SELECTOR, timeout=15_000)
            await page.wait_for_timeout(2_000)

            self.logger.info("Metro results URL: %s", page.url)
            self.save_html(await page.content(), query)

            raw_items: list[dict] = await page.evaluate(
                """(sel) => Array.from(document.querySelectorAll(sel)).map(article => {
                    const linkEl = article.closest('a') || article.parentElement?.closest('a');
                    const imgEl  = article.querySelector('img');
                    return {
                        product_id: article.getAttribute('data-cnstrc-item-id') || '',
                        title:      article.getAttribute('data-cnstrc-item-name') || '',
                        price:      article.getAttribute('data-cnstrc-item-price') || '',
                        link:       linkEl ? (linkEl.getAttribute('href') || '') : '',
                        image:      imgEl  ? (imgEl.getAttribute('src') || '') : '',
                    };
                })""",
                _PRODUCT_SELECTOR,
            )
            self.save_raw_json(raw_items, query)
            return [self._to_candidate(item, query) for item in raw_items if item.get("title")]
        finally:
            await page.close()

    def _to_candidate(self, item: dict, query: str) -> ProductCandidate:
        parsed_price = parse_price(item.get("price", ""))
        price_val = parsed_price.value if (parsed_price and parsed_price.value is not None) else 0.0

        title = item.get("title", "")
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
