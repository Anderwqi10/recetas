import json
import os
import re
from typing import Any

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def build_recipe_prompt(ingredient_names: list[str]) -> str:
    lista = ", ".join(ingredient_names)
    return (
        "Eres un chef experto. El usuario tiene estos ingredientes en casa: "
        f"{lista}.\n\n"
        "Genera UNA receta realista que use principalmente esos ingredientes. "
        "Puedes asumir condimentos básicos (sal, aceite, agua).\n\n"
        "Responde ÚNICAMENTE con un JSON válido (sin markdown) con esta estructura:\n"
        "{\n"
        '  "title": "título de la receta",\n'
        '  "description": "breve descripción",\n'
        '  "ingredients_used": ["ingrediente1", "ingrediente2"],\n'
        '  "steps": ["paso 1", "paso 2", "paso 3"]\n'
        "}"
    )


def _extract_json_block(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_llm_recipe_response(raw: str) -> dict[str, Any]:
    if not raw or not raw.strip():
        raise ValueError("La respuesta del LLM está vacía")

    try:
        data = json.loads(_extract_json_block(raw))
    except json.JSONDecodeError as exc:
        raise ValueError(f"No se pudo parsear JSON del LLM: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("La respuesta debe ser un objeto JSON")

    title = data.get("title")
    if not title or not str(title).strip():
        raise ValueError("Falta el campo 'title' en la respuesta")

    steps = data.get("steps")
    if not isinstance(steps, list) or len(steps) < 1:
        raise ValueError("El campo 'steps' debe ser una lista con al menos un paso")

    ingredients_used = data.get("ingredients_used", [])
    if not isinstance(ingredients_used, list):
        raise ValueError("El campo 'ingredients_used' debe ser una lista")

    return {
        "title": str(title).strip(),
        "description": str(data.get("description", "")).strip(),
        "ingredients_used": [str(i).strip() for i in ingredients_used if str(i).strip()],
        "steps": [str(s).strip() for s in steps if str(s).strip()],
    }


async def call_openrouter(
    prompt: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY no configurada. Añádela al entorno o archivo .env"
        )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost:8000"),
        "X-Title": "Recetas App",
    }
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Formato de respuesta inesperado de OpenRouter") from exc
