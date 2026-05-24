import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

from app.models.common import StoreId
from app.models.product_models import ProductCandidate
from app.utils.logging_utils import get_logger


class BaseScraper(ABC):
    """
    Abstract base for all store scrapers.

    Manages the Playwright browser lifecycle and provides helpers for
    saving debug artifacts (HTML snapshots, screenshots, raw JSON).

    Usage:
        async with PlazaVeaScraper(data_dir=settings.data_dir) as scraper:
            products = await scraper.search_products("arroz")
    """

    def __init__(
        self,
        store_id: StoreId,
        data_dir: Path,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        self.store_id = store_id
        self.data_dir = data_dir
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.logger = get_logger(f"scraper.{store_id.value}")
        self._pw = None
        self._browser: Browser | None = None

    # ── Browser lifecycle ─────────────────────────────────────────────────────

    async def __aenter__(self) -> "BaseScraper":
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.headless)
        self.logger.info("Browser launched (headless=%s)", self.headless)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self.logger.info("Browser closed")

    # ── Interface (subclasses implement this) ─────────────────────────────────

    @abstractmethod
    async def search_products(self, query: str) -> list[ProductCandidate]:
        """
        Search for products matching query and return normalized candidates.

        Must never raise — catch internal errors, log them, and return [].
        """
        ...

    # ── Page helper ───────────────────────────────────────────────────────────

    async def _new_page(self) -> Page:
        """Create a new browser page with the configured timeout."""
        if not self._browser:
            raise RuntimeError(
                f"{self.__class__.__name__} must be used as an async context manager"
            )
        page = await self._browser.new_page()
        page.set_default_timeout(self.timeout_ms)
        return page

    # ── Shared browser helpers ────────────────────────────────────────────────

    async def _dismiss_popups(self, page: Page) -> None:
        """Try to close common modal / cookie popups."""
        selectors = [
            "button:has-text('Aceptar')",
            "button:has-text('Cerrar')",
            "button:has-text('Entendido')",
            "button:has-text('Acepto')",
            "[aria-label='Close']",
            ".close-button",
            ".modal-close",
        ]
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1_000):
                    await btn.click()
                    await page.wait_for_timeout(400)
            except Exception:
                pass

    async def _submit_search(
        self, page: Page, query: str, selectors: tuple[str, ...]
    ) -> None:
        """Find the first visible search box, fill it, and press Enter."""
        for selector in selectors:
            try:
                box = page.locator(selector).first
                if await box.is_visible(timeout=2_000):
                    await box.click()
                    await box.fill(query)
                    await box.press("Enter")
                    self.logger.debug("Search submitted via %s", selector)
                    return
            except Exception:
                continue
        raise RuntimeError(
            f"[{self.store_id.value}] Could not find search box for query={query!r}"
        )

    # ── Artifact saving ───────────────────────────────────────────────────────

    def _artifact_path(self, subdir: str, query: str, ext: str) -> Path:
        """Build a timestamped artifact path and ensure the folder exists."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(" ", "_")[:30]
        folder = self.data_dir / subdir / self.store_id.value
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{safe_query}_{ts}.{ext}"

    def save_html(self, html: str, query: str) -> Path:
        """Save raw HTML snapshot for debugging."""
        path = self._artifact_path("raw_html", query, "html")
        path.write_text(html, encoding="utf-8")
        self.logger.debug("HTML saved → %s", path.name)
        return path

    async def save_screenshot(self, page: Page, query: str) -> Path:
        """Capture a full-page screenshot for debugging."""
        path = self._artifact_path("screenshots", query, "png")
        await page.screenshot(path=str(path), full_page=True)
        self.logger.debug("Screenshot saved → %s", path.name)
        return path

    def save_raw_json(self, data: list[dict], query: str) -> Path:
        """Save raw extracted product dicts before normalization."""
        path = self._artifact_path("raw_json", query, "json")
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.logger.debug("Raw JSON saved → %s", path.name)
        return path
