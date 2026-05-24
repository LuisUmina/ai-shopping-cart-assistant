"""
Scraping orchestrator (Phase 5 wiring).

Runs all preferred stores in parallel for a list of queries.
One Playwright browser per store; queries run sequentially within each browser
to keep memory bounded. A failure in one store never blocks the others.

Windows / ProactorEventLoop note
─────────────────────────────────
Playwright needs ProactorEventLoop to spawn the browser subprocess.
Uvicorn's --reload worker starts with SelectorEventLoop, so setting the
policy in main.py arrives too late. The fix: each store search runs in its
own ThreadPoolExecutor thread (asyncio.to_thread) with a dedicated
ProactorEventLoop created at thread start. This is completely invisible to
callers — the public search() method is still a normal async coroutine.
"""
import asyncio
import sys
from pathlib import Path

from app.models.common import StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.metro_scraper import MetroScraper
from app.scrapers.plaza_vea_scraper import PlazaVeaScraper
from app.scrapers.tottus_scraper import TottusScraper
from app.scrapers.vivanda_scraper import VivandaScraper
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Registry of store → scraper class. Tests may monkeypatch this.
_SCRAPERS: dict[StoreId, type[BaseScraper]] = {
    StoreId.PLAZA_VEA: PlazaVeaScraper,
    StoreId.METRO: MetroScraper,
    StoreId.TOTTUS: TottusScraper,
    StoreId.VIVANDA: VivandaScraper,
}


class ScrapingService:
    """Searches multiple stores in parallel and returns candidates grouped by query."""

    def __init__(
        self,
        data_dir: Path,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        self.data_dir = data_dir
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def search(
        self,
        queries: list[str],
        stores: list[StoreId],
    ) -> dict[str, list[ProductCandidate]]:
        """
        Run each query against every preferred store and aggregate the results.

        Returns {query: [candidates from all stores]}. Unknown stores are skipped.
        Always returns an entry for every requested query (empty list if no hits).
        """
        results: dict[str, list[ProductCandidate]] = {q: [] for q in queries}
        if not queries:
            return results

        active_stores = [s for s in stores if s in _SCRAPERS]
        if not active_stores:
            logger.warning("No active stores to scrape (preferred=%s)", stores)
            return results

        logger.info("Scraping %d queries across %d stores", len(queries), len(active_stores))

        store_results = await asyncio.gather(
            *(self._search_store(s, queries) for s in active_stores),
            return_exceptions=True,
        )

        for r in store_results:
            if isinstance(r, BaseException):
                logger.error("Scraper task failed: %s", r)
                continue
            for query, candidates in r.items():
                results[query].extend(candidates)

        return results

    # ── Per-store helpers ─────────────────────────────────────────────────────

    async def _search_store(
        self, store: StoreId, queries: list[str]
    ) -> dict[str, list[ProductCandidate]]:
        """Offload to a thread so the scraper gets its own event loop (see module doc)."""
        return await asyncio.to_thread(self._run_in_thread, store, queries)

    def _run_in_thread(
        self, store: StoreId, queries: list[str]
    ) -> dict[str, list[ProductCandidate]]:
        """
        Called from a thread-pool thread. Creates a dedicated event loop —
        ProactorEventLoop on Windows, the platform default elsewhere.
        """
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._do_search(store, queries))
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    async def _do_search(
        self, store: StoreId, queries: list[str]
    ) -> dict[str, list[ProductCandidate]]:
        """Async scraping logic that runs inside the per-thread event loop."""
        scraper_cls = _SCRAPERS[store]
        out: dict[str, list[ProductCandidate]] = {q: [] for q in queries}
        try:
            async with scraper_cls(
                data_dir=self.data_dir,
                headless=self.headless,
                timeout_ms=self.timeout_ms,
            ) as scraper:
                for query in queries:
                    # search_products already swallows internal errors → returns [].
                    out[query] = await scraper.search_products(query)
        except Exception as exc:
            logger.error("Browser for %s failed: %s", store.value, exc)
        return out
