import pytest

from app.services.llm import build_recipe_prompt, parse_llm_recipe_response


def test_build_recipe_prompt_includes_all_ingredients():
    ingredients = ["huevo", "tomate", "queso"]
    prompt = build_recipe_prompt(ingredients)
    assert "huevo, tomate, queso" in prompt
    assert "JSON" in prompt
    assert "title" in prompt


def test_parse_llm_recipe_response_valid_json():
    raw = """
    {
      "title": "Tortilla rápida",
      "description": "Una tortilla sencilla",
      "ingredients_used": ["huevo", "patata"],
      "steps": ["Pelar", "Freír", "Servir"]
    }
    """
    data = parse_llm_recipe_response(raw)
    assert data["title"] == "Tortilla rápida"
    assert len(data["steps"]) == 3
    assert "huevo" in data["ingredients_used"]


def test_parse_llm_recipe_response_with_markdown_fence():
    raw = """```json
    {"title": "Ensalada", "description": "", "ingredients_used": ["lechuga"],
     "steps": ["Lavar", "Mezclar"]}
    ```"""
    data = parse_llm_recipe_response(raw)
    assert data["title"] == "Ensalada"


def test_parse_llm_recipe_response_missing_title_raises():
    with pytest.raises(ValueError, match="title"):
        parse_llm_recipe_response('{"steps": ["solo un paso"]}')


def test_parse_llm_recipe_response_invalid_json_raises():
    with pytest.raises(ValueError, match="parsear"):
        parse_llm_recipe_response("esto no es json")
