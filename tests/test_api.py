from unittest.mock import AsyncMock, patch

SAMPLE_LLM_JSON = """
{
  "title": "Revuelto de huevo y tomate",
  "description": "Plato rápido para el día a día",
  "ingredients_used": ["huevo", "tomate"],
  "steps": ["Batir los huevos", "Saltear el tomate", "Mezclar y servir"]
}
"""


def test_api_create_ingredient(client, auth_headers):
    response = client.post(
        "/api/ingredients",
        json={"name": "Huevo", "quantity": "6 unidades"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Huevo"
    assert data["quantity"] == "6 unidades"


def test_api_create_ingredient_duplicate_rejected(client, auth_headers):
    client.post(
        "/api/ingredients",
        json={"name": "Tomate"},
        headers=auth_headers,
    )
    response = client.post(
        "/api/ingredients",
        json={"name": "tomate"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_api_list_ingredients_requires_auth(client):
    response = client.get("/api/ingredients")
    assert response.status_code == 401


@patch("app.routers.recipes.call_openrouter", new_callable=AsyncMock)
def test_api_generate_recipe(mock_openrouter, client, auth_headers):
    mock_openrouter.return_value = SAMPLE_LLM_JSON

    client.post("/api/ingredients", json={"name": "Huevo"}, headers=auth_headers)
    client.post("/api/ingredients", json={"name": "Tomate"}, headers=auth_headers)

    response = client.post("/api/recipes/generate", headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Revuelto de huevo y tomate"
    assert len(data["steps"]) == 3
    mock_openrouter.assert_called_once()


def test_api_generate_recipe_requires_min_ingredients(client, auth_headers):
    client.post("/api/ingredients", json={"name": "Solo uno"}, headers=auth_headers)
    response = client.post("/api/recipes/generate", headers=auth_headers)
    assert response.status_code == 400


@patch("app.routers.recipes.call_openrouter", new_callable=AsyncMock)
def test_api_rate_and_save_recipe(mock_openrouter, client, auth_headers):
    mock_openrouter.return_value = SAMPLE_LLM_JSON
    client.post("/api/ingredients", json={"name": "Huevo"}, headers=auth_headers)
    client.post("/api/ingredients", json={"name": "Tomate"}, headers=auth_headers)
    created = client.post("/api/recipes/generate", headers=auth_headers).json()

    response = client.patch(
        f"/api/recipes/{created['id']}",
        json={"rating": 5, "is_saved": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 5
    assert response.json()["is_saved"] is True


@patch("app.routers.recipes.call_openrouter", new_callable=AsyncMock)
def test_api_delete_recipe(mock_openrouter, client, auth_headers):
    mock_openrouter.return_value = SAMPLE_LLM_JSON
    client.post("/api/ingredients", json={"name": "Huevo"}, headers=auth_headers)
    client.post("/api/ingredients", json={"name": "Tomate"}, headers=auth_headers)
    recipe_id = client.post("/api/recipes/generate", headers=auth_headers).json()["id"]

    response = client.delete(f"/api/recipes/{recipe_id}", headers=auth_headers)
    assert response.status_code == 204
    listed = client.get("/api/recipes", headers=auth_headers).json()
    assert listed["total"] == 0
