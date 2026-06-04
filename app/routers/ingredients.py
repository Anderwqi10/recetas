from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Ingredient, User
from app.schemas import IngredientCreate, IngredientResponse
from app.services.ingredients import (
    IngredientValidationError,
    ingredient_names_conflict,
    validate_ingredient_name,
    validate_quantity,
)

router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientResponse])
def list_ingredients(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Ingredient)
        .filter(Ingredient.user_id == user.id)
        .order_by(Ingredient.name)
        .all()
    )


@router.post("", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    data: IngredientCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        name = validate_ingredient_name(data.name)
        quantity = validate_quantity(data.quantity)
    except IngredientValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    existing = [
        i.name
        for i in db.query(Ingredient).filter(Ingredient.user_id == user.id).all()
    ]
    if ingredient_names_conflict(existing, name):
        raise HTTPException(status_code=400, detail="Ese ingrediente ya está en tu inventario")

    ingredient = Ingredient(user_id=user.id, name=name, quantity=quantity)
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(
    ingredient_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ingredient = (
        db.query(Ingredient)
        .filter(Ingredient.id == ingredient_id, Ingredient.user_id == user.id)
        .first()
    )
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    db.delete(ingredient)
    db.commit()
