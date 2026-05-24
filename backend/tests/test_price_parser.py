import pytest
from app.utils.price_parser import ParsedPrice, parse_price


class TestParsePrice:
    def test_standard_soles(self):
        assert parse_price("S/ 24.90").value == 24.90

    def test_soles_dot_slash(self):
        assert parse_price("S/. 24.90").value == 24.90

    def test_soles_no_space(self):
        assert parse_price("S/.24.90").value == 24.90

    def test_soles_comma_decimal(self):
        assert parse_price("S/ 24,90").value == 24.90

    def test_thousands_separator(self):
        assert parse_price("S/ 1,299.00").value == 1299.00

    def test_bare_number(self):
        assert parse_price("24.90").value == 24.90

    def test_pen_prefix(self):
        assert parse_price("PEN 15.50").value == 15.50

    def test_with_surrounding_text(self):
        assert parse_price("Precio: S/ 8.90 c/u").value == 8.90

    def test_integer_price(self):
        assert parse_price("S/ 5").value == 5.0

    def test_empty_string_returns_none(self):
        assert parse_price("").value is None

    def test_non_numeric_string_returns_none(self):
        assert parse_price("Agotado").value is None

    def test_whitespace_only_returns_none(self):
        assert parse_price("   ").value is None

    def test_currency_is_pen(self):
        result = parse_price("S/ 10.00")
        assert result.currency == "PEN"

    def test_raw_preserved(self):
        raw = "S/ 24.90"
        result = parse_price(raw)
        assert result.raw == raw

    def test_ambiguous_flag_on_multiple_prices(self):
        result = parse_price("S/ 24.90 antes S/ 19.90")
        assert result.ambiguous is True
        assert result.value == 24.90  # first match wins

    def test_single_price_not_ambiguous(self):
        assert parse_price("S/ 24.90").ambiguous is False
