import json

from sqlalchemy.orm import Session

from app.models import Recipe
from app.services.llm import parse_llm_recipe_response


def save_recipe_from_llm(
    db: Session,
    *,
    user_id: int,
    raw_llm: str,
) -> Recipe:
    parsed = parse_llm_recipe_response(raw_llm)
    recipe = Recipe(
        user_id=user_id,
        title=parsed["title"],
        description=parsed["description"],
        steps_json=json.dumps(parsed["steps"], ensure_ascii=False),
        ingredients_used_json=json.dumps(parsed["ingredients_used"], ensure_ascii=False),
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe
