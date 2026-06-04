from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Ingredient, Recipe, User
from app.recipe_store import save_recipe_from_llm
from app.schemas import (
    RecipeGenerateRequest,
    RecipeListResponse,
    RecipeResponse,
    RecipeUpdate,
)
from app.services.llm import build_recipe_prompt, call_openrouter

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=RecipeListResponse)
def list_recipes(
    saved_only: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Recipe).filter(Recipe.user_id == user.id)
    if saved_only:
        q = q.filter(Recipe.is_saved.is_(True))
    recipes = q.order_by(Recipe.created_at.desc()).all()
    return RecipeListResponse(
        items=[RecipeResponse.from_orm_recipe(r) for r in recipes],
        total=len(recipes),
    )


@router.post("/generate", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def generate_recipe(
    body: RecipeGenerateRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ingredients = (
        db.query(Ingredient)
        .filter(Ingredient.user_id == user.id)
        .order_by(Ingredient.name)
        .all()
    )
    if len(ingredients) < 2:
        raise HTTPException(
            status_code=400,
            detail="Añade al menos 2 ingredientes a tu inventario para generar una receta",
        )

    names = [i.name for i in ingredients]
    prompt = build_recipe_prompt(names)
    if body and body.extra_notes:
        prompt += f"\n\nNotas del usuario: {body.extra_notes.strip()}"

    try:
        raw = await call_openrouter(prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al contactar OpenRouter: {exc}",
        ) from exc

    try:
        recipe = save_recipe_from_llm(db, user_id=user.id, raw_llm=raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"La respuesta del LLM no es válida: {exc}",
        ) from exc

    return RecipeResponse.from_orm_recipe(recipe)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = (
        db.query(Recipe)
        .filter(Recipe.id == recipe_id, Recipe.user_id == user.id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")

    if data.rating is not None:
        recipe.rating = data.rating
    if data.is_saved is not None:
        recipe.is_saved = data.is_saved

    db.commit()
    db.refresh(recipe)
    return RecipeResponse.from_orm_recipe(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = (
        db.query(Recipe)
        .filter(Recipe.id == recipe_id, Recipe.user_id == user.id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    db.delete(recipe)
    db.commit()
