import json
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import Recipe


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: str | None = Field(default=None, max_length=40)


class IngredientResponse(BaseModel):
    id: int
    name: str
    quantity: str | None

    model_config = {"from_attributes": True}


class RecipeGenerateRequest(BaseModel):
    extra_notes: str | None = Field(default=None, max_length=500)


class RecipeUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    is_saved: bool | None = None


class RecipeResponse(BaseModel):
    id: int
    title: str
    description: str
    steps: list[str]
    ingredients_used: list[str]
    rating: int | None
    is_saved: bool
    created_at: Any

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_recipe(cls, recipe: Recipe) -> "RecipeResponse":
        return cls(
            id=recipe.id,
            title=recipe.title,
            description=recipe.description or "",
            steps=json.loads(recipe.steps_json),
            ingredients_used=json.loads(recipe.ingredients_used_json),
            rating=recipe.rating,
            is_saved=recipe.is_saved,
            created_at=recipe.created_at,
        )


class RecipeListResponse(BaseModel):
    items: list[RecipeResponse]
    total: int
