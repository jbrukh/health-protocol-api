import pytest


@pytest.mark.asyncio
async def test_create_ingredient(client, auth_headers):
    """Test create ingredient."""
    data = {
        "name": "Chicken Breast",
        "default_amount": 100,
        "default_unit": "g",
        "calories": 165,
        "protein_g": 31,
        "carbs_g": 0,
        "fats_g": 3.6,
        "sodium_mg": 74,
    }
    response = await client.post("/ingredients", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Chicken Breast"
    assert result["calories"] == 165
    assert "id" in result
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_ingredient(client, auth_headers, sample_ingredient):
    """Test get ingredient by ID."""
    response = await client.get(f"/ingredients/{sample_ingredient['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Whey Protein"


@pytest.mark.asyncio
async def test_list_ingredients(client, auth_headers, sample_ingredients):
    """Test list all ingredients."""
    response = await client.get("/ingredients", headers=auth_headers)
    assert response.status_code == 200
    ingredients = response.json()
    assert len(ingredients) == 3


@pytest.mark.asyncio
async def test_search_ingredients(client, auth_headers, sample_ingredients):
    """Test search ingredients by name."""
    response = await client.get("/ingredients/search?q=protein", headers=auth_headers)
    assert response.status_code == 200
    ingredients = response.json()
    assert len(ingredients) == 1
    assert ingredients[0]["name"] == "Whey Protein"


@pytest.mark.asyncio
async def test_search_ingredients_case_insensitive(client, auth_headers, sample_ingredients):
    """Test search is case insensitive."""
    response = await client.get("/ingredients/search?q=PROTEIN", headers=auth_headers)
    assert response.status_code == 200
    ingredients = response.json()
    assert len(ingredients) == 1


@pytest.mark.asyncio
async def test_update_ingredient(client, auth_headers, sample_ingredient):
    """Test update ingredient."""
    update_data = {"calories": 130, "protein_g": 25}
    response = await client.put(
        f"/ingredients/{sample_ingredient['id']}",
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["calories"] == 130
    assert result["protein_g"] == 25


@pytest.mark.asyncio
async def test_delete_ingredient(client, auth_headers, sample_ingredient):
    """Test delete ingredient."""
    response = await client.delete(f"/ingredients/{sample_ingredient['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/ingredients/{sample_ingredient['id']}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_ingredient_name(client, auth_headers, sample_ingredient):
    """Test duplicate name returns 409."""
    data = {
        "name": "Whey Protein",
        "default_amount": 1,
        "default_unit": "scoop",
        "calories": 120,
        "protein_g": 24,
        "carbs_g": 3,
        "fats_g": 1,
        "sodium_mg": 50,
    }
    response = await client.post("/ingredients", json=data, headers=auth_headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_nonexistent_ingredient(client, auth_headers):
    """Test get non-existent ingredient returns 404."""
    response = await client.get("/ingredients/99999", headers=auth_headers)
    assert response.status_code == 404
