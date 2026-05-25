"""
Tests for store scraper normalization logic.

The `_to_candidate` methods are tested directly with sample raw data
so no Playwright / browser is required.
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.product_models import ProductCandidate
from app.scrapers.metro_scraper import MetroScraper
from app.scrapers.plaza_vea_scraper import PlazaVeaScraper
from app.scrapers.tottus_scraper import TottusScraper
from app.scrapers.vivanda_scraper import VivandaScraper


# ── Fixtures: sample raw data mirroring live HTML ─────────────────────────────

PLAZA_VEA_ITEM = {
    "title": "Arroz Extra FARAON Bolsa 750g",
    "brand": "FARAON",
    "category": "Abarrotes / Arroz / Arroz Extra",
    "product_id": "28252",
    "stock": "true",
    "ga_price": "3.5",
    "sale_price": "3.50",
    "link": "/arroz-extra-faraon-bolsa-750g/p",
    "image": "https://plazavea.vteximg.com.br/arquivos/ids/34333602-184-184/20139618.jpg",
    "presentation": "Bolsa 750g",
}

METRO_ITEM = {
    "product_id": "528",
    "title": "Arroz Gran Reserva Extra Valle Norte Bolsa 5 Kg",
    "price": "22.9",
    "link": "/arroz-extra-valle-norte-mejorado-bolsa-5-kg-107169-2/p",
    "image": "https://metroio.vtexassets.com/arquivos/ids/237894-144-144",
}

TOTTUS_ITEM = {
    "productId": "113706045",
    "displayName": "Arroz Extra Tottus Bolsa 5 Kg",
    "url": "https://www.tottus.com.pe/tottus-pe/articulo/113706045/arroz-extra-tottus-bolsa-5-kg",
    "brand": "TOTTUS",
    "mediaUrls": ["https://media.tottus.com.pe/tottusPE/40275956_1/public"],
    "measurements": {"format": "Bolsa 5 Kg"},
    "prices": [
        {"label": "", "symbol": "S/ ", "crossed": False, "type": "internetPrice", "price": ["18.90"]},
        {"label": "", "symbol": "S/ ", "crossed": True, "type": "normalPrice", "price": ["19.90"]},
    ],
}

VIVANDA_ITEM = {
    "@type": "Product",
    "name": "Arroz Costeño Arroz Extra Bolsa 750g",
    "url": "https://www.vivanda.com.pe/arroz-costeno-extra-bolsa-750g/p",
    "image": ["https://assets.bo-management.cord.pe/public/images/test.jpg"],
    "brand": {"@type": "Brand", "name": "COSTEÑO"},
    "sku": "12345",
    "offers": {
        "@type": "Offer",
        "price": "5.9",
        "priceCurrency": "PEN",
        "availability": "https://schema.org/InStock",
    },
}


# ── Helper: create scraper without browser ────────────────────────────────────

def _pv(tmp_path: Path) -> PlazaVeaScraper:
    return PlazaVeaScraper(data_dir=tmp_path)


def _metro(tmp_path: Path) -> MetroScraper:
    return MetroScraper(data_dir=tmp_path)


def _tottus(tmp_path: Path) -> TottusScraper:
    return TottusScraper(data_dir=tmp_path)


def _vivanda(tmp_path: Path) -> VivandaScraper:
    return VivandaScraper(data_dir=tmp_path)


# ── Plaza Vea ─────────────────────────────────────────────────────────────────

class TestPlazaVeaNormalization:
    def test_returns_product_candidate(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert isinstance(c, ProductCandidate)

    def test_store_id(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.store == StoreId.PLAZA_VEA

    def test_title(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.title == "Arroz Extra FARAON Bolsa 750g"

    def test_price(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.price == pytest.approx(3.50)

    def test_quantity_parsed_from_presentation(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.quantity_value == pytest.approx(0.75)  # 750g → 0.75 kg
        assert c.quantity_unit == QuantityUnit.KG

    def test_unit_price(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.unit_price == pytest.approx(3.50 / 0.75, rel=1e-3)

    def test_availability_available(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.availability == Availability.AVAILABLE

    def test_availability_unavailable(self, tmp_path: Path):
        item = {**PLAZA_VEA_ITEM, "stock": "false"}
        c = _pv(tmp_path)._to_candidate(item, "arroz")
        assert c.availability == Availability.UNAVAILABLE

    def test_link_becomes_absolute(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.product_url.startswith("https://www.plazavea.com.pe")

    def test_brand(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.brand == "FARAON"

    def test_search_query_preserved(self, tmp_path: Path):
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz costeño")
        assert c.search_query == "arroz costeño"

    def test_scraped_at_is_recent(self, tmp_path: Path):
        before = datetime.now(timezone.utc)
        c = _pv(tmp_path)._to_candidate(PLAZA_VEA_ITEM, "arroz")
        assert c.scraped_at >= before

    def test_fallback_to_ga_price_if_no_sale_price(self, tmp_path: Path):
        item = {**PLAZA_VEA_ITEM, "sale_price": ""}
        c = _pv(tmp_path)._to_candidate(item, "arroz")
        assert c.price == pytest.approx(3.50)

    def test_missing_title_handled_as_empty(self, tmp_path: Path):
        item = {**PLAZA_VEA_ITEM, "title": ""}
        # _to_candidate is called only when title is truthy; calling directly is still valid
        c = _pv(tmp_path)._to_candidate(item, "arroz")
        assert c.title == ""


# ── Metro ─────────────────────────────────────────────────────────────────────

class TestMetroNormalization:
    def test_returns_product_candidate(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert isinstance(c, ProductCandidate)

    def test_store_id(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert c.store == StoreId.METRO

    def test_title(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert "Valle Norte" in c.title

    def test_price(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert c.price == pytest.approx(22.9)

    def test_quantity_parsed_from_title(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert c.quantity_value == pytest.approx(5.0)
        assert c.quantity_unit == QuantityUnit.KG

    def test_unit_price(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert c.unit_price == pytest.approx(22.9 / 5.0, rel=1e-3)

    def test_link_becomes_absolute(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert c.product_url.startswith("https://www.metro.pe")

    def test_availability_default_unknown(self, tmp_path: Path):
        c = _metro(tmp_path)._to_candidate(METRO_ITEM, "arroz")
        assert c.availability == Availability.UNKNOWN

    def test_absolute_link_unchanged(self, tmp_path: Path):
        item = {**METRO_ITEM, "link": "https://www.metro.pe/product/123"}
        c = _metro(tmp_path)._to_candidate(item, "arroz")
        assert c.product_url == "https://www.metro.pe/product/123"

    def test_fallback_unit_when_no_quantity_in_title(self, tmp_path: Path):
        item = {**METRO_ITEM, "title": "Arroz genérico"}
        c = _metro(tmp_path)._to_candidate(item, "arroz")
        assert c.quantity_value == pytest.approx(1.0)
        assert c.quantity_unit == QuantityUnit.UNIT


# ── Tottus ────────────────────────────────────────────────────────────────────

class TestTottusNormalization:
    def test_returns_product_candidate(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert isinstance(c, ProductCandidate)

    def test_store_id(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.store == StoreId.TOTTUS

    def test_title(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.title == "Arroz Extra Tottus Bolsa 5 Kg"

    def test_uses_internet_price_not_crossed(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.price == pytest.approx(18.90)

    def test_quantity_from_measurements_format(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.quantity_value == pytest.approx(5.0)
        assert c.quantity_unit == QuantityUnit.KG

    def test_unit_price(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.unit_price == pytest.approx(18.90 / 5.0, rel=1e-3)

    def test_brand(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.brand == "TOTTUS"

    def test_product_url(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert "tottus.com.pe" in c.product_url

    def test_image_url(self, tmp_path: Path):
        c = _tottus(tmp_path)._to_candidate(TOTTUS_ITEM, "arroz")
        assert c.image_url == "https://media.tottus.com.pe/tottusPE/40275956_1/public"

    def test_fallback_when_no_crossed_price(self, tmp_path: Path):
        item = {**TOTTUS_ITEM, "prices": [
            {"crossed": False, "type": "internetPrice", "price": ["15.90"]}
        ]}
        c = _tottus(tmp_path)._to_candidate(item, "arroz")
        assert c.price == pytest.approx(15.90)

    def test_empty_prices_gives_zero(self, tmp_path: Path):
        item = {**TOTTUS_ITEM, "prices": []}
        c = _tottus(tmp_path)._to_candidate(item, "arroz")
        assert c.price == 0.0

    def test_fallback_unit_when_no_measurement(self, tmp_path: Path):
        item = {**TOTTUS_ITEM, "measurements": {}, "displayName": "Arroz genérico"}
        c = _tottus(tmp_path)._to_candidate(item, "arroz")
        assert c.quantity_value == pytest.approx(1.0)
        assert c.quantity_unit == QuantityUnit.UNIT


# ── Vivanda ───────────────────────────────────────────────────────────────────

class TestVivandaNormalization:
    def test_returns_product_candidate(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert isinstance(c, ProductCandidate)

    def test_store_id(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.store == StoreId.VIVANDA

    def test_title(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert "Costeño" in c.title

    def test_price(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.price == pytest.approx(5.9)

    def test_quantity_from_title(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.quantity_value == pytest.approx(0.75)  # 750g → 0.75 kg
        assert c.quantity_unit == QuantityUnit.KG

    def test_availability_in_stock(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.availability == Availability.AVAILABLE

    def test_availability_out_of_stock(self, tmp_path: Path):
        item = {**VIVANDA_ITEM, "offers": {**VIVANDA_ITEM["offers"], "availability": "https://schema.org/OutOfStock"}}
        c = _vivanda(tmp_path)._to_candidate(item, "arroz")
        assert c.availability == Availability.UNAVAILABLE

    def test_availability_unknown_when_empty(self, tmp_path: Path):
        item = {**VIVANDA_ITEM, "offers": {**VIVANDA_ITEM["offers"], "availability": ""}}
        c = _vivanda(tmp_path)._to_candidate(item, "arroz")
        assert c.availability == Availability.UNKNOWN

    def test_brand_from_nested_dict(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.brand == "COSTEÑO"

    def test_sku_as_product_id(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.product_id == "12345"

    def test_image_from_list(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert c.image_url is not None
        assert c.image_url.startswith("https://")

    def test_image_as_string_fallback(self, tmp_path: Path):
        item = {**VIVANDA_ITEM, "image": "https://example.com/img.jpg"}
        c = _vivanda(tmp_path)._to_candidate(item, "arroz")
        assert c.image_url == "https://example.com/img.jpg"

    def test_product_url(self, tmp_path: Path):
        c = _vivanda(tmp_path)._to_candidate(VIVANDA_ITEM, "arroz")
        assert "vivanda.com.pe" in c.product_url
