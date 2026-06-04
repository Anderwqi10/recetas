import pytest

from app.services.ingredients import (
    IngredientValidationError,
    ingredient_names_conflict,
    normalize_ingredient_name,
    validate_ingredient_name,
    validate_quantity,
)


def test_validate_ingredient_name_empty():
    with pytest.raises(IngredientValidationError, match="vacío"):
        validate_ingredient_name("   ")


def test_validate_ingredient_name_too_short():
    with pytest.raises(IngredientValidationError, match="al menos"):
        validate_ingredient_name("a")


def test_validate_ingredient_name_invalid_characters():
    with pytest.raises(IngredientValidationError, match="no permitidos"):
        validate_ingredient_name("tomate<script>")


def test_normalize_ingredient_name_strips_spaces():
    assert normalize_ingredient_name("  huevo   fresco  ") == "huevo fresco"


def test_ingredient_names_conflict_detects_duplicates():
    existing = ["Tomate", "Cebolla"]
    assert ingredient_names_conflict(existing, "tomate") is True
    assert ingredient_names_conflict(existing, "Ajo") is False


def test_validate_quantity_max_length():
    with pytest.raises(IngredientValidationError):
        validate_quantity("x" * 50)
