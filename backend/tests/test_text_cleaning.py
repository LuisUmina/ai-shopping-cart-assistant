from app.utils.text_cleaning import (
    clean_title,
    normalize_for_comparison,
    remove_accents,
    tokenize,
)


class TestRemoveAccents:
    def test_tilde_n(self):
        assert remove_accents("Costeño") == "Costeno"

    def test_accent_e(self):
        assert remove_accents("Leché") == "Leche"

    def test_no_accents_unchanged(self):
        assert remove_accents("Arroz") == "Arroz"


class TestNormalizeForComparison:
    def test_lowercase_and_no_accents(self):
        assert normalize_for_comparison("Arroz Costeño") == "arroz costeno"

    def test_collapses_whitespace(self):
        assert normalize_for_comparison("  arroz   5  kg  ") == "arroz 5 kg"

    def test_uppercase_lowered(self):
        assert normalize_for_comparison("GLORIA") == "gloria"


class TestCleanTitle:
    def test_strips_trailing_punctuation(self):
        assert clean_title("Arroz Costeño.") == "Arroz Costeño"

    def test_collapses_spaces(self):
        assert clean_title("Arroz   Extra   5  kg") == "Arroz Extra 5 kg"

    def test_preserves_accents(self):
        assert "Costeño" in clean_title("Arroz Costeño 5 kg")

    def test_empty_string(self):
        assert clean_title("") == ""


class TestTokenize:
    def test_basic(self):
        assert tokenize("Arroz 5 kg") == ["arroz", "5", "kg"]

    def test_accents_removed(self):
        assert "costeno" in tokenize("Arroz Costeño")

    def test_splits_on_slash(self):
        assert tokenize("leche/yogurt") == ["leche", "yogurt"]

    def test_splits_on_dash(self):
        assert tokenize("coca-cola") == ["coca", "cola"]

    def test_empty_tokens_removed(self):
        tokens = tokenize("  arroz  ")
        assert "" not in tokens
