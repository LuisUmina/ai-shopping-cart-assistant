from datetime import datetime, timezone
from pathlib import Path

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper
from app.utils.price_parser import parse_price
from app.utils.unit_parser import parse_quantity

_BASE_URL = "https://www.tottus.com.pe"
_SEARCH_SELECTORS = (
    "input[placeholder*='Busca']",
    "input[placeholder*='busca']",
    "input[type='search']",
    "header input",
)


class TottusScraper(BaseScraper):
    def __init__(
        self,
        data_dir: Path,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        super().__init__(
            store_id=StoreId.TOTTUS,
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

            # Wait for __NEXT_DATA__ to be populated with search results
            await page.wait_for_function(
                """() => {
                    const el = document.getElementById('__NEXT_DATA__');
                    if (!el) return false;
                    try {
                        const data = JSON.parse(el.textContent);
                        return Array.isArray(data?.props?.pageProps?.results)
                            && data.props.pageProps.results.length > 0;
                    } catch { return false; }
                }""",
                timeout=15_000,
            )
            await page.wait_for_timeout(1_000)

            self.logger.info("Tottus results URL: %s", page.url)
            self.save_html(await page.content(), query)

            results: list[dict] = await page.evaluate(
                """() => {
                    const el = document.getElementById('__NEXT_DATA__');
                    const data = JSON.parse(el.textContent);
                    return data.props.pageProps.results || [];
                }"""
            )
            self.save_raw_json(results, query)
            return [self._to_candidate(item, query) for item in results if item.get("displayName")]
        finally:
            await page.close()

    def _to_candidate(self, item: dict, query: str) -> ProductCandidate:
        # Find the non-crossed (internet) price
        price_str = ""
        for price_entry in item.get("prices", []):
            if not price_entry.get("crossed", True):
                values = price_entry.get("price", [])
                price_str = values[0] if values else ""
                break

        parsed_price = parse_price(price_str)
        price_val = parsed_price.value if (parsed_price and parsed_price.value is not None) else 0.0

        title = item.get("displayName", "")
        format_text = item.get("measurements", {}).get("format", "")
        presentation = format_text or title
        parsed_qty = parse_quantity(presentation)
        qty_value = parsed_qty.value if (parsed_qty and parsed_qty.value) else 1.0
        qty_unit = parsed_qty.unit if (parsed_qty and parsed_qty.unit) else QuantityUnit.UNIT
        unit_price = round(price_val / qty_value, 4) if qty_value else price_val

        media = item.get("mediaUrls", [])
        image_url = media[0] if media else None

        return ProductCandidate(
            store=StoreId.TOTTUS,
            product_id=item.get("productId") or None,
            title=title,
            brand=item.get("brand") or None,
            raw_price=price_str or None,
            price=price_val,
            presentation_text=presentation,
            quantity_value=qty_value,
            quantity_unit=qty_unit,
            unit_price=unit_price,
            unit_price_unit=qty_unit,
            availability=Availability.AVAILABLE,
            image_url=image_url,
            product_url=item.get("url", ""),
            search_query=query,
            scraped_at=datetime.now(timezone.utc),
        )
