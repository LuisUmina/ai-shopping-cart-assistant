import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper
from app.utils.price_parser import parse_price
from app.utils.unit_parser import parse_quantity

_BASE_URL = "https://www.vivanda.com.pe"


class VivandaScraper(BaseScraper):
    """
    Vivanda uses Next.js with JSON-LD structured data (ItemList) on search pages.
    URL pattern: /search/{query}
    """

    def __init__(
        self,
        data_dir: Path,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        super().__init__(
            store_id=StoreId.VIVANDA,
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
        search_url = f"{_BASE_URL}/search/{quote(query)}"
        page = await self._new_page()
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            await page.wait_for_timeout(3_000)
            await self._dismiss_popups(page)

            # Wait for JSON-LD ItemList to be populated with products
            await page.wait_for_function(
                """() => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const s of scripts) {
                        try {
                            const d = JSON.parse(s.textContent);
                            if (d['@type'] === 'ItemList' && d.itemListElement?.length > 0) return true;
                        } catch {}
                    }
                    return false;
                }""",
                timeout=15_000,
            )

            self.logger.info("Vivanda results URL: %s", page.url)
            self.save_html(await page.content(), query)

            items: list[dict] = await page.evaluate(
                """() => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const s of scripts) {
                        try {
                            const d = JSON.parse(s.textContent);
                            if (d['@type'] === 'ItemList' && d.itemListElement?.length > 0)
                                return d.itemListElement.map(e => e.item || e);
                        } catch {}
                    }
                    return [];
                }"""
            )
            self.save_raw_json(items, query)
            return [self._to_candidate(item, query) for item in items if item.get("name")]
        finally:
            await page.close()

    def _to_candidate(self, item: dict, query: str) -> ProductCandidate:
        offers = item.get("offers", {})
        price_str = str(offers.get("price", ""))
        parsed_price = parse_price(price_str)
        price_val = parsed_price.value if (parsed_price and parsed_price.value is not None) else 0.0

        title = item.get("name", "")
        parsed_qty = parse_quantity(title)
        qty_value = parsed_qty.value if (parsed_qty and parsed_qty.value) else 1.0
        qty_unit = parsed_qty.unit if (parsed_qty and parsed_qty.unit) else QuantityUnit.UNIT
        unit_price = round(price_val / qty_value, 4) if qty_value else price_val

        schema_avail = offers.get("availability", "")
        availability = (
            Availability.AVAILABLE
            if "InStock" in schema_avail
            else Availability.UNAVAILABLE if schema_avail else Availability.UNKNOWN
        )

        images = item.get("image", [])
        image_url = images[0] if isinstance(images, list) and images else (
            images if isinstance(images, str) else None
        )

        brand_info = item.get("brand", {})
        brand = brand_info.get("name") if isinstance(brand_info, dict) else None

        return ProductCandidate(
            store=StoreId.VIVANDA,
            product_id=item.get("sku") or None,
            title=title,
            brand=brand,
            raw_price=price_str or None,
            price=price_val,
            presentation_text=title,
            quantity_value=qty_value,
            quantity_unit=qty_unit,
            unit_price=unit_price,
            unit_price_unit=qty_unit,
            availability=availability,
            image_url=image_url,
            product_url=item.get("url", ""),
            search_query=query,
            scraped_at=datetime.now(timezone.utc),
        )
