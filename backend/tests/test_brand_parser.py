from app.utils.brand_parser import extract_brand
from app.utils.text_cleaning import normalize_for_comparison


class TestExtractBrand:
    def test_known_brand_high_confidence(self):
        result = extract_brand("Arroz Costeño Extra 5 kg")
        assert result.brand is not None
        assert "costeno" in normalize_for_comparison(result.brand)
        assert result.confidence == 0.9

    def test_known_brand_gloria(self):
        result = extract_brand("Leche Gloria Entera 1 l")
        assert result.brand is not None
        assert "loria" in result.brand
        assert result.confidence == 0.9

    def test_known_brand_case_insensitive(self):
        result = extract_brand("LECHE GLORIA ENTERA")
        assert result.confidence == 0.9

    def test_unknown_brand_heuristic(self):
        result = extract_brand("Arroz Paisanito Premium 5 kg")
        assert result.brand is not None
        assert result.confidence == 0.3

    def test_empty_title_returns_none(self):
        result = extract_brand("")
        assert result.brand is None
        assert result.confidence == 0.0

    def test_multi_word_brand(self):
        result = extract_brand("Aceite San Fernando 1 l")
        assert result.brand is not None
        assert "san fernando" in normalize_for_comparison(result.brand)
        assert result.confidence == 0.9

    def test_raw_preserved(self):
        title = "Arroz Costeño 5 kg"
        result = extract_brand(title)
        assert result.raw == title
