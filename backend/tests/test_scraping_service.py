"""
Tests for ScrapingService — orchestration only, no real browsers.

The real scraper classes are swapped out via monkeypatch with a fake that
returns canned results, so these tests run in milliseconds.
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.services import scraping_service
from app.services.scraping_service import ScrapingService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _candidate(title: str, store: StoreId = StoreId.PLAZA_VEA) -> ProductCandidate:
    return ProductCandidate(
        store=store,
        title=title,
        price=10.0,
        presentation_text="Bolsa 1 kg",
        quantity_value=1.0,
        quantity_unit=QuantityUnit.KG,
        unit_price=10.0,
        availability=Availability.AVAILABLE,
        product_url="https://example.com/p",
        search_query="x",
        scraped_at=datetime.now(timezone.utc),
    )


def make_fake_scraper(
    results_by_query: dict[str, list[ProductCandidate]] | None = None,
    fail_on_enter: bool = False,
    fail_on_search: bool = False,
) -> type:
    """Build a FakeScraper class matching the BaseScraper async-context interface."""
    results = results_by_query or {}

    class FakeScraper:
        def __init__(self, data_dir, headless: bool = True, timeout_ms: int = 30_000):
            pass

        async def __aenter__(self):
            if fail_on_enter:
                raise RuntimeError("Browser launch failed")
            return self

        async def __aexit__(self, *_):
            return None

        async def search_products(self, query: str) -> list[ProductCandidate]:
            if fail_on_search:
                # Real scrapers swallow internal errors and return []. Match that.
                return []
            return results.get(query, [])

    return FakeScraper


def _patch_scrapers(monkeypatch, mapping: dict[StoreId, type]) -> None:
    monkeypatch.setattr(scraping_service, "_SCRAPERS", mapping)


# ── ScrapingService.search ────────────────────────────────────────────────────

class TestScrapingServiceSearch:
    async def test_empty_queries_returns_empty_dict(self, tmp_path: Path):
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search([], [StoreId.PLAZA_VEA])
        assert result == {}

    async def test_no_active_stores_returns_empty_lists(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {})  # registry has no scrapers
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(["arroz"], [StoreId.PLAZA_VEA])
        assert result == {"arroz": []}

    async def test_single_store_single_query(self, monkeypatch, tmp_path: Path):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper({"arroz": [_candidate("PV Arroz")]}),
        })
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(["arroz"], [StoreId.PLAZA_VEA])
        assert len(result["arroz"]) == 1
        assert result["arroz"][0].title == "PV Arroz"

    async def test_aggregates_results_across_stores(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper(
                {"arroz": [_candidate("PV Arroz", StoreId.PLAZA_VEA)]}
            ),
            StoreId.METRO: make_fake_scraper(
                {"arroz": [_candidate("Metro Arroz", StoreId.METRO)]}
            ),
        })
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(
            ["arroz"], [StoreId.PLAZA_VEA, StoreId.METRO]
        )
        assert len(result["arroz"]) == 2
        titles = {c.title for c in result["arroz"]}
        assert titles == {"PV Arroz", "Metro Arroz"}

    async def test_multiple_queries_grouped_by_query(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper({
                "arroz": [_candidate("PV Arroz")],
                "leche": [_candidate("PV Leche"), _candidate("PV Leche Gloria")],
            }),
        })
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(["arroz", "leche"], [StoreId.PLAZA_VEA])
        assert len(result["arroz"]) == 1
        assert len(result["leche"]) == 2

    async def test_unknown_store_silently_skipped(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper({"arroz": [_candidate("PV")]}),
        })
        svc = ScrapingService(data_dir=tmp_path)
        # METRO is requested but not in the registry — should be skipped
        result = await svc.search(["arroz"], [StoreId.PLAZA_VEA, StoreId.METRO])
        assert len(result["arroz"]) == 1

    async def test_browser_launch_failure_isolated(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper({"arroz": [_candidate("PV")]}),
            StoreId.METRO: make_fake_scraper(fail_on_enter=True),
        })
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(["arroz"], [StoreId.PLAZA_VEA, StoreId.METRO])
        # PV result still arrives, Metro contributes nothing — no exception raised
        assert len(result["arroz"]) == 1

    async def test_every_query_has_an_entry_even_when_empty(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper({"arroz": [_candidate("PV")]}),
        })
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(["arroz", "papel"], [StoreId.PLAZA_VEA])
        assert "arroz" in result
        assert "papel" in result
        assert result["papel"] == []

    async def test_failing_scraper_does_not_break_query_for_other_stores(
        self, monkeypatch, tmp_path: Path
    ):
        _patch_scrapers(monkeypatch, {
            StoreId.PLAZA_VEA: make_fake_scraper(fail_on_search=True),
            StoreId.METRO: make_fake_scraper({"arroz": [_candidate("Metro")]}),
        })
        svc = ScrapingService(data_dir=tmp_path)
        result = await svc.search(["arroz"], [StoreId.PLAZA_VEA, StoreId.METRO])
        assert len(result["arroz"]) == 1
        assert result["arroz"][0].title == "Metro"
