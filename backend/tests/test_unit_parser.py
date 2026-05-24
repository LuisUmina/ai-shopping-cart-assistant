import pytest
from app.models.common import QuantityUnit
from app.utils.unit_parser import (
    ParsedQuantity,
    are_compatible,
    calculate_required_units,
    normalize_quantity,
    parse_quantity,
    to_base_value,
)


class TestNormalizeQuantity:
    def test_grams_to_kg(self):
        v, u = normalize_quantity(750, QuantityUnit.G)
        assert v == 0.75
        assert u == QuantityUnit.KG

    def test_1000g_to_1kg(self):
        v, u = normalize_quantity(1000, QuantityUnit.G)
        assert v == 1.0
        assert u == QuantityUnit.KG

    def test_ml_to_l(self):
        v, u = normalize_quantity(900, QuantityUnit.ML)
        assert v == 0.9
        assert u == QuantityUnit.L

    def test_1000ml_to_1l(self):
        v, u = normalize_quantity(1000, QuantityUnit.ML)
        assert v == 1.0
        assert u == QuantityUnit.L

    def test_kg_unchanged(self):
        v, u = normalize_quantity(5, QuantityUnit.KG)
        assert v == 5
        assert u == QuantityUnit.KG

    def test_l_unchanged(self):
        v, u = normalize_quantity(2, QuantityUnit.L)
        assert v == 2
        assert u == QuantityUnit.L

    def test_unit_unchanged(self):
        v, u = normalize_quantity(6, QuantityUnit.UNIT)
        assert v == 6
        assert u == QuantityUnit.UNIT


class TestAreCompatible:
    def test_mass_compatible(self):
        assert are_compatible(QuantityUnit.G, QuantityUnit.KG)

    def test_volume_compatible(self):
        assert are_compatible(QuantityUnit.ML, QuantityUnit.L)

    def test_count_compatible(self):
        assert are_compatible(QuantityUnit.UNIT, QuantityUnit.PACK)

    def test_mass_volume_incompatible(self):
        assert not are_compatible(QuantityUnit.KG, QuantityUnit.L)

    def test_mass_count_incompatible(self):
        assert not are_compatible(QuantityUnit.KG, QuantityUnit.UNIT)


class TestCalculateRequiredUnits:
    def test_exact_match(self):
        result = calculate_required_units(5, QuantityUnit.KG, 5, QuantityUnit.KG)
        assert result == (1, 5000.0, 0.0)

    def test_multiple_units_needed(self):
        # want 5 kg, product is 1 kg
        result = calculate_required_units(5, QuantityUnit.KG, 1, QuantityUnit.KG)
        assert result[0] == 5  # 5 units needed
        assert result[2] == 0.0  # no excess

    def test_overshoot(self):
        # want 1 l, product is 600 ml → need 2 units, excess = 200 ml
        result = calculate_required_units(1, QuantityUnit.L, 600, QuantityUnit.ML)
        assert result[0] == 2  # ceil(1000/600)
        assert result[2] == pytest.approx(200.0)

    def test_unit_conversion_grams(self):
        # want 5 kg, product is 500 g
        result = calculate_required_units(5, QuantityUnit.KG, 500, QuantityUnit.G)
        assert result[0] == 10  # 5000g / 500g

    def test_incompatible_units_returns_none(self):
        assert calculate_required_units(1, QuantityUnit.KG, 1, QuantityUnit.L) is None

    def test_count_units(self):
        # want 12 units, product is a pack of 4
        result = calculate_required_units(12, QuantityUnit.UNIT, 4, QuantityUnit.PACK)
        assert result[0] == 3


class TestParseQuantity:
    def test_kg(self):
        r = parse_quantity("Arroz 5 kg")
        assert r.value == 5.0
        assert r.unit == QuantityUnit.KG

    def test_grams_normalized(self):
        # 750 g → 0.75 kg
        r = parse_quantity("750g")
        assert r.value == 0.75
        assert r.unit == QuantityUnit.KG

    def test_ml_normalized(self):
        # 900 ml → 0.9 l
        r = parse_quantity("Leche 900 ml")
        assert r.value == pytest.approx(0.9)
        assert r.unit == QuantityUnit.L

    def test_litros_spanish(self):
        r = parse_quantity("2 litros")
        assert r.value == 2.0
        assert r.unit == QuantityUnit.L

    def test_pack_x_count(self):
        r = parse_quantity("Pack x 6")
        assert r.value == 6.0
        assert r.unit == QuantityUnit.UNIT

    def test_unidades_spanish(self):
        r = parse_quantity("x 6 unidades")
        assert r.value == 6.0
        assert r.unit == QuantityUnit.UNIT

    def test_promotion_flagged(self):
        r = parse_quantity("2x1")
        assert r.is_promotion is True
        assert r.value is None

    def test_promotion_3x2_flagged(self):
        r = parse_quantity("Detergente 3x2")
        assert r.is_promotion is True

    def test_empty_returns_none(self):
        r = parse_quantity("")
        assert r.value is None
        assert r.unit is None

    def test_no_unit_returns_none(self):
        r = parse_quantity("Arroz Costeño Premium")
        assert r.value is None

    def test_ambiguous_flagged(self):
        # Two quantity+unit combos in same string
        r = parse_quantity("Aceite 1 l x 2 litros")
        assert r.ambiguous is True

    def test_bolsa_unit(self):
        r = parse_quantity("Bolsa 5 kg")
        assert r.value == 5.0
        assert r.unit == QuantityUnit.KG

    def test_rollo(self):
        r = parse_quantity("12 rollos")
        assert r.value == 12.0
        assert r.unit == QuantityUnit.ROLL

    def test_caja(self):
        r = parse_quantity("Caja 24 unidades")
        assert r.value == 24.0
        assert r.unit == QuantityUnit.UNIT

    def test_decimal_comma(self):
        r = parse_quantity("1,5 kg")
        assert r.value == 1.5
        assert r.unit == QuantityUnit.KG
