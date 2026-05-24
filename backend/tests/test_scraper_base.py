"""
Tests for BaseScraper infrastructure.

Uses a DummyScraper that skips the real browser launch so these tests
run without Playwright browser binaries installed.
(Browser binaries are needed starting Phase 5 — run:
 python -m playwright install chromium)
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.base_scraper import BaseScraper


# ── DummyScraper — no real browser ────────────────────────────────────────────

def _make_candidate(query: str) -> ProductCandidate:
    return ProductCandidate(
        store=StoreId.PLAZA_VEA,
        title=f"Producto {query} test",
        price=9.90,
        presentation_text="1 kg",
        quantity_value=1.0,
        quantity_unit=QuantityUnit.KG,
        unit_price=9.90,
        availability=Availability.AVAILABLE,
        product_url="https://example.com/product",
        search_query=query,
        scraped_at=datetime.now(timezone.utc),
    )


class DummyScraper(BaseScraper):
    """Concrete scraper for testing — bypasses browser launch."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__(
            store_id=StoreId.PLAZA_VEA,
            data_dir=data_dir,
            headless=True,
        )

    async def __aenter__(self) -> "DummyScraper":
        # Skip Playwright launch so tests run without browser binaries.
        self.logger.info("DummyScraper entered (no real browser)")
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    async def search_products(self, query: str) -> list[ProductCandidate]:
        return [_make_candidate(query)]


class FailingScraper(DummyScraper):
    """Scraper that simulates an internal failure."""

    async def search_products(self, query: str) -> list[ProductCandidate]:
        try:
            raise RuntimeError("Simulated network error")
        except RuntimeError:
            self.logger.error("Search failed for %r — returning empty", query)
            return []


# ── Interface tests ───────────────────────────────────────────────────────────

class TestDummyScraper:
    async def test_returns_list_of_product_candidates(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            results = await scraper.search_products("arroz")
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], ProductCandidate)

    async def test_product_query_matches(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            results = await scraper.search_products("leche")
        assert results[0].search_query == "leche"

    async def test_store_id_is_set(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            results = await scraper.search_products("arroz")
        assert results[0].store == StoreId.PLAZA_VEA

    async def test_failing_scraper_returns_empty_not_raises(self, tmp_path: Path):
        async with FailingScraper(data_dir=tmp_path) as scraper:
            results = await scraper.search_products("arroz")
        assert results == []


# ── Artifact saving tests ─────────────────────────────────────────────────────

class TestArtifactSaving:
    async def test_save_html_creates_file(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            path = scraper.save_html("<html>test</html>", "arroz")
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "<html>test</html>"

    async def test_save_html_in_correct_folder(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            path = scraper.save_html("<html/>", "arroz")
        assert "raw_html" in str(path)
        assert "plaza_vea" in str(path)

    async def test_save_raw_json_creates_file(self, tmp_path: Path):
        data = [{"title": "Arroz test", "price": 9.90}]
        async with DummyScraper(data_dir=tmp_path) as scraper:
            path = scraper.save_raw_json(data, "arroz")
        assert path.exists()
        assert path.suffix == ".json"

    async def test_save_raw_json_content_valid(self, tmp_path: Path):
        import json
        data = [{"title": "Leche Gloria", "price": 4.50}]
        async with DummyScraper(data_dir=tmp_path) as scraper:
            path = scraper.save_raw_json(data, "leche")
        parsed = json.loads(path.read_text(encoding="utf-8"))
        assert parsed[0]["title"] == "Leche Gloria"

    async def test_folders_created_automatically(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            scraper.save_html("<html/>", "arroz")
            scraper.save_raw_json([], "arroz")
        assert (tmp_path / "raw_html" / "plaza_vea").is_dir()
        assert (tmp_path / "raw_json" / "plaza_vea").is_dir()

    async def test_artifact_filename_contains_query(self, tmp_path: Path):
        async with DummyScraper(data_dir=tmp_path) as scraper:
            path = scraper.save_html("<html/>", "papel higienico")
        assert "papel_higienico" in path.name

    async def test_two_saves_produce_unique_files(self, tmp_path: Path):
        import time
        async with DummyScraper(data_dir=tmp_path) as scraper:
            p1 = scraper.save_html("<html>1</html>", "arroz")
            time.sleep(1)  # ensure different timestamps
            p2 = scraper.save_html("<html>2</html>", "arroz")
        assert p1 != p2


# ── Safety tests ──────────────────────────────────────────────────────────────

class TestSafety:
    async def test_new_page_raises_without_context_manager(self, tmp_path: Path):
        # Instantiate without entering context — _browser is None.
        scraper = DummyScraper(data_dir=tmp_path)
        # DummyScraper skips browser setup, so _browser stays None.
        with pytest.raises(RuntimeError, match="context manager"):
            await scraper._new_page()

    def test_store_id_is_correct_type(self, tmp_path: Path):
        scraper = DummyScraper(data_dir=tmp_path)
        assert isinstance(scraper.store_id, StoreId)

    def test_data_dir_stored(self, tmp_path: Path):
        scraper = DummyScraper(data_dir=tmp_path)
        assert scraper.data_dir == tmp_path
