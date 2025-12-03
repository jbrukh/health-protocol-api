import pytest


@pytest.mark.asyncio
async def test_create_recipe(client, auth_headers, sample_ingredients):
    """Test create recipe with items."""
    data = {
        "name": "Test Recipe",
        "items": [
            {"ingredient_id": sample_ingredients[0]["id"], "amount": 2, "unit": "scoop"},
        ],
    }
    response = await client.post("/recipes", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Test Recipe"
    assert len(result["items"]) == 1
    assert result["totals"]["calories"] == 240
    assert result["totals"]["protein_g"] == 48


@pytest.mark.asyncio
async def test_get_recipe(client, auth_headers, sample_recipe):
    """Test get recipe by ID."""
    response = await client.get(f"/recipes/{sample_recipe['id']}", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Protein Shake"
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_list_recipes(client, auth_headers, sample_recipe):
    """Test list recipes."""
    response = await client.get("/recipes", headers=auth_headers)
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1


@pytest.mark.asyncio
async def test_recipe_computed_totals(client, auth_headers, sample_recipe):
    """Test recipe totals are computed correctly."""
    response = await client.get(f"/recipes/{sample_recipe['id']}", headers=auth_headers)
    result = response.json()
    assert result["totals"]["calories"] > 0
    assert result["totals"]["protein_g"] > 0


@pytest.mark.asyncio
async def test_add_recipe_item(client, auth_headers, sample_recipe, sample_ingredients):
    """Test add item to recipe."""
    data = {"ingredient_id": sample_ingredients[0]["id"], "amount": 1, "unit": "scoop"}
    response = await client.post(
        f"/recipes/{sample_recipe['id']}/items",
        json=data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["items"]) == 4


@pytest.mark.asyncio
async def test_update_recipe_item(client, auth_headers, sample_recipe):
    """Test update recipe item."""
    item_id = sample_recipe["items"][0]["id"]
    data = {"amount": 2}
    response = await client.put(
        f"/recipes/{sample_recipe['id']}/items/{item_id}",
        json=data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    updated_item = next(i for i in result["items"] if i["id"] == item_id)
    assert updated_item["amount"] == 2


@pytest.mark.asyncio
async def test_delete_recipe_item(client, auth_headers, sample_recipe):
    """Test delete recipe item."""
    item_id = sample_recipe["items"][0]["id"]
    response = await client.delete(
        f"/recipes/{sample_recipe['id']}/items/{item_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_delete_recipe(client, auth_headers, sample_recipe):
    """Test delete recipe."""
    response = await client.delete(f"/recipes/{sample_recipe['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/recipes/{sample_recipe['id']}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recipe_with_nonexistent_ingredient(client, auth_headers):
    """Test create recipe with non-existent ingredient returns 404."""
    data = {
        "name": "Bad Recipe",
        "items": [{"ingredient_id": 99999, "amount": 1, "unit": "scoop"}],
    }
    response = await client.post("/recipes", json=data, headers=auth_headers)
    assert response.status_code == 404
