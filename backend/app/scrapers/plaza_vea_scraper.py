from datetime import datetime, timezone
from pathlib import Path

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper
from app.utils.price_parser import parse_price
from app.utils.unit_parser import parse_quantity

_BASE_URL = "https://www.plazavea.com.pe"
_SEARCH_SELECTORS = (
    "input[placeholder*='Busca']",
    "input[type='search']",
    "input[name='search-box']",
    "header input",
)
_PRODUCT_SELECTOR = "[class*='ga-product-item']"


class PlazaVeaScraper(BaseScraper):
    def __init__(
        self,
        data_dir: Path,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        super().__init__(
            store_id=StoreId.PLAZA_VEA,
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

            self.logger.info("Plaza Vea results URL: %s", page.url)
            self.save_html(await page.content(), query)

            raw_items: list[dict] = await page.evaluate(
                """(sel) => Array.from(document.querySelectorAll(sel)).map(el => {
                    const saleEl = el.querySelector('.Showcase__salePrice');
                    const linkEl = el.querySelector('a.Showcase__link');
                    const imgEl  = el.querySelector('img.showcase__image');
                    const presEl = el.querySelector('.Showcase__units-reference');
                    return {
                        title:        el.getAttribute('data-ga-name') || '',
                        brand:        el.getAttribute('data-ga-brand') || '',
                        category:     el.getAttribute('data-ga-category') || '',
                        product_id:   el.getAttribute('data-sku') || '',
                        stock:        el.getAttribute('data-stock') || '',
                        ga_price:     el.getAttribute('data-ga-price') || '',
                        sale_price:   saleEl ? (saleEl.getAttribute('data-price') || '') : '',
                        link:         linkEl ? (linkEl.getAttribute('href') || '') : '',
                        image:        imgEl  ? (imgEl.getAttribute('src')  || '') : '',
                        presentation: presEl ? (presEl.textContent || '').trim() : '',
                    };
                })""",
                _PRODUCT_SELECTOR,
            )
            self.save_raw_json(raw_items, query)
            return [self._to_candidate(item, query) for item in raw_items if item.get("title")]
        finally:
            await page.close()

    def _to_candidate(self, item: dict, query: str) -> ProductCandidate:
        price_raw = item.get("sale_price") or item.get("ga_price", "")
        parsed_price = parse_price(price_raw)
        price_val = parsed_price.value if (parsed_price and parsed_price.value is not None) else 0.0

        presentation = item.get("presentation", "")
        parsed_qty = parse_quantity(presentation)
        qty_value = parsed_qty.value if (parsed_qty and parsed_qty.value) else 1.0
        qty_unit = parsed_qty.unit if (parsed_qty and parsed_qty.unit) else QuantityUnit.UNIT
        unit_price = round(price_val / qty_value, 4) if qty_value else price_val

        stock = item.get("stock", "").lower()
        availability = (
            Availability.AVAILABLE if stock == "true"
            else Availability.UNAVAILABLE if stock == "false"
            else Availability.UNKNOWN
        )
        link = item.get("link", "")
        if link and not link.startswith("http"):
            link = _BASE_URL + link

        return ProductCandidate(
            store=StoreId.PLAZA_VEA,
            product_id=item.get("product_id") or None,
            title=item["title"],
            brand=item.get("brand") or None,
            category=item.get("category") or None,
            raw_price=price_raw or None,
            price=price_val,
            presentation_text=presentation,
            quantity_value=qty_value,
            quantity_unit=qty_unit,
            unit_price=unit_price,
            unit_price_unit=qty_unit,
            availability=availability,
            image_url=item.get("image") or None,
            product_url=link,
            search_query=query,
            scraped_at=datetime.now(timezone.utc),
        )
