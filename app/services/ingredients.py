import re
import unicodedata

MIN_INGREDIENT_LEN = 2
MAX_INGREDIENT_LEN = 80
MAX_QUANTITY_LEN = 40

_NAME_PATTERN = re.compile(r"^[\w\s\-áéíóúñüÁÉÍÓÚÑÜ.,()/]+$", re.UNICODE)


class IngredientValidationError(ValueError):
    pass


def normalize_ingredient_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name.strip())
    return re.sub(r"\s+", " ", name)


def validate_ingredient_name(name: str) -> str:
    if not name or not name.strip():
        raise IngredientValidationError("El nombre del ingrediente no puede estar vacío")

    normalized = normalize_ingredient_name(name)

    if len(normalized) < MIN_INGREDIENT_LEN:
        raise IngredientValidationError(
            f"El nombre debe tener al menos {MIN_INGREDIENT_LEN} caracteres"
        )

    if len(normalized) > MAX_INGREDIENT_LEN:
        raise IngredientValidationError(
            f"El nombre no puede superar {MAX_INGREDIENT_LEN} caracteres"
        )

    if not _NAME_PATTERN.match(normalized):
        raise IngredientValidationError(
            "El nombre contiene caracteres no permitidos"
        )

    return normalized


def validate_quantity(quantity: str | None) -> str | None:
    if quantity is None or not str(quantity).strip():
        return None
    q = str(quantity).strip()
    if len(q) > MAX_QUANTITY_LEN:
        raise IngredientValidationError(
            f"La cantidad no puede superar {MAX_QUANTITY_LEN} caracteres"
        )
    return q


def ingredient_names_conflict(existing: list[str], new_name: str) -> bool:
    key = normalize_ingredient_name(new_name).casefold()
    return any(normalize_ingredient_name(n).casefold() == key for n in existing)
