# Health Tracker API — Final Specification

## Overview

A lightweight Python/FastAPI REST API for single-user food, macro, exercise, and body measurement tracking. Uses SQLite on Railway with persistent storage. Designed for Claude Skill integration.

**Key Features:**
- Track foods, macros, and calories against configurable targets
- Save reusable ingredients and recipes (recipes expand to individual food entries)
- Log exercises with structured + unstructured data
- Track daily weight and waist measurements
- Query today's progress, remaining budget, and historical trends
- Claude Skill for natural language interaction

---

## Database Schema

### 1. `user_profile` (Single Row)

Stores user info and macro/calorie target ranges.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Always 1 |
| `birthdate` | DATE | User's birthdate (age computed) |
| `height_inches` | REAL | Height in inches |
| `calories_min` | INTEGER | Daily calorie minimum |
| `calories_max` | INTEGER | Daily calorie maximum |
| `protein_min_g` | INTEGER | Protein minimum (grams) |
| `protein_max_g` | INTEGER | Protein maximum (grams) |
| `carbs_min_g` | INTEGER | Carbs minimum (grams) |
| `carbs_max_g` | INTEGER | Carbs maximum (grams) |
| `fats_min_g` | INTEGER | Fats minimum (grams) |
| `fats_max_g` | INTEGER | Fats maximum (grams) |
| `sodium_max_mg` | INTEGER | Sodium maximum (mg) |
| `updated_at` | TIMESTAMP | Last update |

---

### 2. `ingredients` (Reusable Ingredient Definitions)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `name` | TEXT UNIQUE | e.g., "Whey Protein Scoop" |
| `default_amount` | REAL | e.g., 1 |
| `default_unit` | TEXT | e.g., "scoop", "medium", "g" |
| `calories` | INTEGER | Per default amount |
| `protein_g` | REAL | Per default amount |
| `carbs_g` | REAL | Per default amount |
| `fats_g` | REAL | Per default amount |
| `sodium_mg` | INTEGER | Per default amount |
| `created_at` | TIMESTAMP | |

---

### 3. `recipes` (Recipe Metadata)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `name` | TEXT UNIQUE | e.g., "Protein Shake" |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

---

### 4. `recipe_items` (Recipe → Ingredient Junction)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `recipe_id` | INTEGER FK | → recipes.id (CASCADE DELETE) |
| `ingredient_id` | INTEGER FK | → ingredients.id |
| `amount` | REAL | Quantity in recipe |
| `unit` | TEXT | Unit for this usage |

---

### 5. `foods` (Logged Food Entries)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `date` | DATE | Date logged |
| `marker` | TEXT | Distinct label (e.g., "breakfast_shake") |
| `name` | TEXT | Food/ingredient name |
| `amount` | REAL | Quantity consumed |
| `unit` | TEXT | Unit |
| `calories` | INTEGER | Calories (immutable snapshot) |
| `protein_g` | REAL | Protein (immutable snapshot) |
| `carbs_g` | REAL | Carbs (immutable snapshot) |
| `fats_g` | REAL | Fats (immutable snapshot) |
| `sodium_mg` | INTEGER | Sodium (immutable snapshot) |
| `ingredient_id` | INTEGER NULL | FK → ingredients (if from ingredient) |
| `recipe_id` | INTEGER NULL | FK → recipes (if from recipe expansion) |
| `created_at` | TIMESTAMP | |

**Indexes**: `(date)`, `(date, marker)`

---

### 6. `daily_snapshots` (Historical Macro Summaries)

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE PRIMARY KEY | The day |
| `calories` | INTEGER | Total calories |
| `protein_g` | REAL | Total protein |
| `carbs_g` | REAL | Total carbs |
| `fats_g` | REAL | Total fats |
| `sodium_mg` | INTEGER | Total sodium |
| `snapshot_at` | TIMESTAMP | When snapshot was created |

**Note**: Snapshots are generated lazily when historical data is requested.

---

### 7. `body_measurements` (Weight & Waist Tracking)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `date` | DATE | Date of measurement |
| `time` | TIME | Time of measurement |
| `weight_lbs` | REAL NULL | Weight in pounds |
| `waist_cm` | REAL NULL | Waist in centimeters |
| `created_at` | TIMESTAMP | |

**Note**: Multiple entries per day allowed (e.g., morning vs evening). Either field can be null if only one was measured.

**Indexes**: `(date)`

---

### 8. `exercises` (Exercise Log)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `date` | DATE | Date of exercise |
| `exercise_type` | TEXT | e.g., "walk", "weights", "run" |
| `duration_minutes` | INTEGER | Time spent |
| `details` | JSON | Unstructured data |
| `created_at` | TIMESTAMP | |

**Example `details` JSON**:
```json
// Walk
{"miles": 3.2, "active_calories": 280, "pace_min_per_mile": 14.5}

// Weightlifting
{"workout_name": "Workout 1", "notes": "Chest and triceps"}

// Run
{"miles": 5.0, "avg_heart_rate": 155, "calories": 520}
```

---

## API Endpoints

### Authentication

All endpoints (except `/health`) require header:
```
Authorization: Bearer <HEALTH_TRACKER_API_TOKEN>
```

---

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/profile` | Get profile (includes computed age) |
| `PUT` | `/profile` | Update profile |

**GET `/profile` response**:
```json
{
  "birthdate": "1990-05-15",
  "age": 34,
  "height_inches": 70,
  "targets": {
    "calories_min": 1800,
    "calories_max": 2200,
    "protein_min_g": 150,
    "protein_max_g": 180,
    "carbs_min_g": 150,
    "carbs_max_g": 200,
    "fats_min_g": 50,
    "fats_max_g": 70,
    "sodium_max_mg": 2300
  },
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### Ingredients

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingredients` | Create ingredient |
| `GET` | `/ingredients` | List all ingredients |
| `GET` | `/ingredients/{id}` | Get ingredient by ID |
| `GET` | `/ingredients/search?q=whey` | Search by name |
| `PUT` | `/ingredients/{id}` | Update ingredient (future logs only) |
| `DELETE` | `/ingredients/{id}` | Delete ingredient |

**POST `/ingredients` request**:
```json
{
  "name": "Whey Protein Scoop",
  "default_amount": 1,
  "default_unit": "scoop",
  "calories": 120,
  "protein_g": 24,
  "carbs_g": 3,
  "fats_g": 1,
  "sodium_mg": 50
}
```

---

### Recipes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/recipes` | Create recipe (with items) |
| `GET` | `/recipes` | List all recipes (with computed macros) |
| `GET` | `/recipes/{id}` | Get recipe with items and totals |
| `PUT` | `/recipes/{id}` | Update recipe name |
| `POST` | `/recipes/{id}/items` | Add item to recipe |
| `PUT` | `/recipes/{id}/items/{item_id}` | Update item in recipe |
| `DELETE` | `/recipes/{id}/items/{item_id}` | Remove item from recipe |
| `DELETE` | `/recipes/{id}` | Delete recipe |

**POST `/recipes` request**:
```json
{
  "name": "Protein Shake",
  "items": [
    {"ingredient_id": 1, "amount": 1, "unit": "scoop"},
    {"ingredient_id": 2, "amount": 1.5, "unit": "cup"},
    {"ingredient_id": 3, "amount": 1, "unit": "medium"}
  ]
}
```

**GET `/recipes/{id}` response**:
```json
{
  "id": 1,
  "name": "Protein Shake",
  "items": [
    {
      "id": 1,
      "ingredient_id": 1,
      "ingredient_name": "Whey Protein Scoop",
      "amount": 1,
      "unit": "scoop",
      "calories": 120,
      "protein_g": 24,
      "carbs_g": 3,
      "fats_g": 1,
      "sodium_mg": 50
    },
    {
      "id": 2,
      "ingredient_id": 2,
      "ingredient_name": "Almond Milk",
      "amount": 1.5,
      "unit": "cup",
      "calories": 45,
      "protein_g": 1.5,
      "carbs_g": 1.5,
      "fats_g": 3.75,
      "sodium_mg": 270
    }
  ],
  "totals": {
    "calories": 270,
    "protein_g": 26.8,
    "carbs_g": 31.5,
    "fats_g": 5.15,
    "sodium_mg": 380
  },
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-10T08:00:00Z"
}
```

---

### Foods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/foods` | Log a food entry directly |
| `POST` | `/foods/from-recipe` | Log from recipe (expands to entries) |
| `GET` | `/foods?date=YYYY-MM-DD` | Get foods for a date |
| `GET` | `/foods?date=YYYY-MM-DD&marker=breakfast_shake` | Filter by marker |
| `PUT` | `/foods/{id}` | Update a food entry |
| `DELETE` | `/foods/{id}` | Delete a food entry |
| `DELETE` | `/foods/by-marker?date=YYYY-MM-DD&marker=breakfast_shake` | Delete all with marker |
| `DELETE` | `/foods/clear?date=YYYY-MM-DD` | Clear all foods for date |

**POST `/foods` request** (direct entry):
```json
{
  "date": "2025-01-15",
  "marker": "breakfast_eggs",
  "name": "Scrambled Eggs",
  "amount": 2,
  "unit": "large",
  "calories": 140,
  "protein_g": 12,
  "carbs_g": 1,
  "fats_g": 10,
  "sodium_mg": 140
}
```

**POST `/foods/from-recipe` request**:
```json
{
  "recipe_id": 1,
  "date": "2025-01-15",
  "marker": "breakfast_shake",
  "scale": 1.0
}
```

**Recipe expansion behavior**: Creates one `foods` row per recipe item, all sharing the same `marker` and `recipe_id`. Macros are scaled and stored immutably at log time.

---

### Body Measurements

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/body` | Log a measurement |
| `GET` | `/body?date=YYYY-MM-DD` | Get measurements for a date |
| `GET` | `/body/latest` | Get most recent measurement |
| `PUT` | `/body/{id}` | Update a measurement |
| `DELETE` | `/body/{id}` | Delete a measurement |

**POST `/body` request**:
```json
{
  "date": "2025-01-15",
  "time": "07:30:00",
  "weight_lbs": 185.5,
  "waist_cm": 86.0
}
```

**Note**: `weight_lbs` and `waist_cm` are both optional (can log just one).

---

### Macros

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/macros/today` | Today's totals + % of targets |
| `GET` | `/macros/remaining` | Remaining budget for today |
| `GET` | `/macros/history?days=7` | Last N days (macros + body measurements) |

**GET `/macros/today` response**:
```json
{
  "date": "2025-01-15",
  "totals": {
    "calories": 1450,
    "protein_g": 95.5,
    "carbs_g": 120.0,
    "fats_g": 55.0,
    "sodium_mg": 1800
  },
  "targets": {
    "calories": {
      "min": 1800,
      "max": 2200,
      "current": 1450,
      "percent_of_min": 80.6
    },
    "protein_g": {
      "min": 150,
      "max": 180,
      "current": 95.5,
      "percent_of_min": 63.7
    },
    "carbs_g": {
      "min": 150,
      "max": 200,
      "current": 120.0,
      "percent_of_min": 80.0
    },
    "fats_g": {
      "min": 50,
      "max": 70,
      "current": 55.0,
      "percent_of_min": 110.0
    },
    "sodium_mg": {
      "max": 2300,
      "current": 1800,
      "percent_of_max": 78.3
    }
  }
}
```

**GET `/macros/remaining` response**:
```json
{
  "date": "2025-01-15",
  "remaining": {
    "calories": {"min": 350, "max": 750},
    "protein_g": {"min": 54.5, "max": 84.5},
    "carbs_g": {"min": 30.0, "max": 80.0},
    "fats_g": {"min": 0, "max": 15.0, "note": "minimum already met"},
    "sodium_mg": {"max": 500}
  },
  "suggestion": "You need at least 54.5g more protein. Consider a high-protein option."
}
```

**GET `/macros/history?days=7` response**:
```json
{
  "days": [
    {
      "date": "2025-01-15",
      "macros": {
        "calories": 1950,
        "protein_g": 155.0,
        "carbs_g": 180.0,
        "fats_g": 62.0,
        "sodium_mg": 2100
      },
      "body": {
        "weight_lbs": 185.5,
        "waist_cm": 86.0,
        "measurements": [
          {"time": "07:30:00", "weight_lbs": 185.5, "waist_cm": 86.0}
        ]
      }
    },
    {
      "date": "2025-01-14",
      "macros": {
        "calories": 2050,
        "protein_g": 160.0,
        "carbs_g": 190.0,
        "fats_g": 65.0,
        "sodium_mg": 2200
      },
      "body": {
        "weight_lbs": 186.0,
        "waist_cm": null,
        "measurements": [
          {"time": "08:00:00", "weight_lbs": 186.0, "waist_cm": null}
        ]
      }
    }
  ]
}
```

**Note**: For days with multiple body measurements, `weight_lbs` and `waist_cm` at the day level show the first measurement of the day. Full list in `measurements` array.

---

### Exercises

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/exercises` | Log an exercise |
| `GET` | `/exercises?date=YYYY-MM-DD` | Get exercises for date |
| `GET` | `/exercises/history?days=7` | Last N days |
| `PUT` | `/exercises/{id}` | Update exercise |
| `DELETE` | `/exercises/{id}` | Delete exercise |

**POST `/exercises` request**:
```json
{
  "date": "2025-01-15",
  "exercise_type": "walk",
  "duration_minutes": 45,
  "details": {
    "miles": 3.2,
    "active_calories": 280,
    "total_calories": 320,
    "pace_min_per_mile": 14.1
  }
}
```

---

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `DELETE` | `/admin/clear-foods` | Clear all foods |
| `DELETE` | `/admin/clear-exercises` | Clear all exercises |
| `DELETE` | `/admin/clear-snapshots` | Clear all snapshots |
| `DELETE` | `/admin/clear-body` | Clear all body measurements |
| `DELETE` | `/admin/clear-all` | Nuclear: clear everything except profile |
| `GET` | `/health` | Health check (no auth required) |

---

## Project Structure

```
health-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, middleware, startup
│   ├── config.py               # Settings (env vars)
│   ├── auth.py                 # API token dependency
│   ├── database.py             # SQLite connection, schema init
│   ├── models/
│   │   ├── __init__.py
│   │   ├── profile.py          # Profile Pydantic models
│   │   ├── ingredient.py       # Ingredient models
│   │   ├── recipe.py           # Recipe models
│   │   ├── food.py             # Food models
│   │   ├── macro.py            # Macro response models
│   │   ├── body.py             # Body measurement models
│   │   └── exercise.py         # Exercise models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   ├── ingredients.py
│   │   ├── recipes.py
│   │   ├── foods.py
│   │   ├── macros.py
│   │   ├── body.py
│   │   ├── exercises.py
│   │   └── admin.py
│   └── services/
│       ├── __init__.py
│       ├── profile_service.py
│       ├── ingredient_service.py
│       ├── recipe_service.py
│       ├── food_service.py
│       ├── macro_service.py
│       ├── snapshot_service.py
│       ├── body_service.py
│       └── exercise_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures, test DB setup
│   ├── test_profile.py
│   ├── test_ingredients.py
│   ├── test_recipes.py
│   ├── test_foods.py
│   ├── test_macros.py
│   ├── test_body.py
│   ├── test_exercises.py
│   └── test_integration.py     # End-to-end flows
├── skill/
│   └── SKILL.md                # Claude skill definition
├── requirements.txt
├── Dockerfile
├── railway.toml
└── README.md
```

---

## Testing Strategy

### Tools
- `pytest` — test framework
- `pytest-asyncio` — async test support
- `httpx` — async HTTP client for API tests
- `pytest-cov` — coverage reporting

### Test Categories

**1. Unit Tests (per service)**
- `test_profile_service.py` — get, update, age calculation
- `test_ingredient_service.py` — CRUD, search
- `test_recipe_service.py` — CRUD, macro computation, item management
- `test_food_service.py` — CRUD, batch delete, recipe expansion with scaling
- `test_macro_service.py` — daily totals, remaining, % calculations
- `test_snapshot_service.py` — lazy generation, idempotency
- `test_body_service.py` — CRUD, multiple per day, latest
- `test_exercise_service.py` — CRUD, JSON details

**2. Router/API Tests (per endpoint)**
- Test each endpoint with valid/invalid inputs
- Test auth (missing token, invalid token)
- Test 404s, validation errors
- Test query parameter filtering

**3. Integration Tests**
- Full flow: create ingredient → create recipe → log recipe → check macros
- History flow: log foods + body measurements over multiple days → request history → verify snapshots + body data
- Delete flow: log foods → delete by marker → verify macros updated

### Test Database
- Each test uses a fresh in-memory SQLite database (`:memory:`)
- Fixtures in `conftest.py` provide:
  - `test_db` — initialized database
  - `test_client` — FastAPI TestClient with auth header
  - `sample_profile` — default user profile with targets
  - `sample_ingredients` — common test ingredients
  - `sample_recipe` — test recipe with items

### Coverage Target
- Aim for >90% coverage on services
- All happy paths and common error cases covered

---

## Implementation Plan (for Claude Code)

### Phase 1: Project Foundation
**Goal**: Working FastAPI app with database and auth

**Tasks**:
1. Create project directory structure as shown above
2. Create `requirements.txt`:
   ```
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   pydantic==2.5.3
   pydantic-settings==2.1.0
   pytest==7.4.4
   pytest-asyncio==0.23.3
   pytest-cov==4.1.0
   httpx==0.26.0
   aiosqlite==0.19.0
   ```
3. Implement `app/config.py`:
   - Use `pydantic-settings` to load `HEALTH_TRACKER_API_TOKEN` and `HEALTH_TRACKER_DATABASE_PATH` from environment
   - Default `HEALTH_TRACKER_DATABASE_PATH` to `./data/health.db` for local dev
4. Implement `app/database.py`:
   - Async SQLite connection using `aiosqlite`
   - `init_db()` function that creates all 8 tables with proper constraints
   - `get_db()` async context manager for connections
5. Implement `app/auth.py`:
   - FastAPI `Depends` function that validates `Authorization: Bearer <token>`
   - Raise `HTTPException(401)` if invalid
6. Implement `app/main.py`:
   - Create FastAPI app with title "Health Tracker API"
   - Add startup event to call `init_db()`
   - Add `/health` endpoint (no auth)
   - Include CORS middleware for local testing
7. Create `Dockerfile`:
   - Use `python:3.11-slim`
   - Copy app, install requirements
   - Create `/data` directory for SQLite
   - Run with `uvicorn`
8. Create `railway.toml` with build and deploy config
9. Write tests in `tests/test_main.py`:
   - Test `/health` returns 200
   - Test protected endpoint returns 401 without token
   - Test protected endpoint returns 401 with wrong token

### Phase 2: Profile Feature
**Goal**: User can set and retrieve profile with macro targets

**Tasks**:
1. Create `app/models/profile.py`:
   - `ProfileResponse` — full profile with computed `age`
   - `ProfileUpdate` — all fields optional for partial updates
2. Implement `app/services/profile_service.py`:
   - `get_profile()` — return profile or create default if none exists
   - `update_profile()` — upsert profile data
   - Helper to compute age from birthdate
3. Implement `app/routers/profile.py`:
   - `GET /profile` — returns `ProfileResponse`
   - `PUT /profile` — accepts `ProfileUpdate`, returns `ProfileResponse`
4. Register router in `main.py`
5. Write tests in `tests/test_profile.py`:
   - Test get returns default profile on first call
   - Test update profile
   - Test partial update (only some fields)
   - Test age calculation from birthdate

### Phase 3: Ingredients Feature
**Goal**: CRUD for reusable ingredients

**Tasks**:
1. Create `app/models/ingredient.py`:
   - `IngredientCreate` — required fields for creation
   - `IngredientResponse` — includes `id` and `created_at`
   - `IngredientUpdate` — all fields optional
2. Implement `app/services/ingredient_service.py`:
   - `create_ingredient()`
   - `get_ingredient(id)`
   - `list_ingredients()`
   - `search_ingredients(query)` — case-insensitive name search
   - `update_ingredient(id, data)`
   - `delete_ingredient(id)`
3. Implement `app/routers/ingredients.py` — all endpoints per spec
4. Register router in `main.py`
5. Write tests in `tests/test_ingredients.py`:
   - Test CRUD operations
   - Test search functionality
   - Test duplicate name returns 409
   - Test delete non-existent returns 404

### Phase 4: Recipes Feature
**Goal**: Recipes as collections of ingredients with computed macros

**Tasks**:
1. Create `app/models/recipe.py`:
   - `RecipeItemCreate` — ingredient_id, amount, unit
   - `RecipeItemResponse` — includes ingredient name and computed macros
   - `RecipeCreate` — name and list of items
   - `RecipeResponse` — includes items and computed totals
   - `RecipeUpdate` — name only
2. Implement `app/services/recipe_service.py`:
   - `create_recipe(name, items)` — create recipe and items in transaction
   - `get_recipe(id)` — includes items with ingredient details
   - `list_recipes()` — all recipes with computed totals
   - `update_recipe(id, name)`
   - `add_recipe_item(recipe_id, item)`
   - `update_recipe_item(recipe_id, item_id, data)`
   - `delete_recipe_item(recipe_id, item_id)`
   - `delete_recipe(id)` — cascades to items
   - `compute_recipe_totals(items)` — sum macros from items
3. Implement `app/routers/recipes.py` — all endpoints per spec
4. Register router in `main.py`
5. Write tests in `tests/test_recipes.py`:
   - Test create recipe with items
   - Test computed totals are accurate
   - Test add/remove items updates totals
   - Test delete recipe cascades
   - Test recipe with non-existent ingredient returns 404

### Phase 5: Foods Feature
**Goal**: Log foods directly or from recipes

**Tasks**:
1. Create `app/models/food.py`:
   - `FoodCreate` — direct food entry
   - `FoodFromRecipe` — recipe_id, date, marker, optional scale
   - `FoodResponse` — full food entry
   - `FoodUpdate` — all fields optional
2. Implement `app/services/food_service.py`:
   - `create_food(data)` — direct entry
   - `create_foods_from_recipe(recipe_id, date, marker, scale)`:
     - Fetch recipe with items
     - Create one food entry per item
     - Scale macros by `scale` parameter
     - All entries share same marker and recipe_id
   - `get_foods(date, marker=None)` — filter by date and optionally marker
   - `update_food(id, data)`
   - `delete_food(id)`
   - `delete_foods_by_marker(date, marker)`
   - `clear_foods_by_date(date)`
3. Implement `app/routers/foods.py` — all endpoints per spec
4. Register router in `main.py`
5. Write tests in `tests/test_foods.py`:
   - Test direct food logging
   - Test recipe expansion creates correct number of entries
   - Test recipe expansion with scale=0.5 halves macros
   - Test filter by date and marker
   - Test delete by marker deletes all matching
   - Test clear by date

### Phase 6: Body Measurements Feature
**Goal**: Track weight and waist measurements

**Tasks**:
1. Create `app/models/body.py`:
   - `BodyMeasurementCreate` — date, time, optional weight_lbs, optional waist_cm
   - `BodyMeasurementResponse` — includes id and created_at
   - `BodyMeasurementUpdate` — all fields optional
2. Implement `app/services/body_service.py`:
   - `create_measurement(data)`
   - `get_measurements(date)` — all measurements for a date
   - `get_latest_measurement()` — most recent by date/time
   - `get_measurements_range(start_date, end_date)` — for history
   - `update_measurement(id, data)`
   - `delete_measurement(id)`
3. Implement `app/routers/body.py` — all endpoints per spec
4. Register router in `main.py`
5. Write tests in `tests/test_body.py`:
   - Test create measurement
   - Test multiple measurements per day
   - Test get latest
   - Test partial measurement (weight only, waist only)

### Phase 7: Macros Feature
**Goal**: Compute daily totals, remaining budget, and history with body data

**Tasks**:
1. Create `app/models/macro.py`:
   - `MacroTotals` — calories, protein_g, carbs_g, fats_g, sodium_mg
   - `MacroTargetStatus` — min, max, current, percent
   - `MacroTodayResponse` — totals and targets with percentages
   - `MacroRemainingResponse` — remaining amounts per macro
   - `MacroHistoryDay` — date, macros, body measurements
   - `MacroHistoryResponse` — list of days
2. Implement `app/services/snapshot_service.py`:
   - `compute_snapshot(date)` — sum all foods for date
   - `get_or_create_snapshot(date)` — return existing or compute
   - `generate_missing_snapshots(start_date, end_date)` — batch create
3. Implement `app/services/macro_service.py`:
   - `get_today_macros()`:
     - Compute current totals from foods table (not snapshot)
     - Fetch profile targets
     - Calculate percentages
   - `get_remaining_macros()`:
     - Get today's totals
     - Subtract from targets
     - Add helpful notes (e.g., "minimum met")
   - `get_macro_history(days)`:
     - Generate missing snapshots for date range
     - Fetch snapshots
     - Fetch body measurements for same range
     - Combine into response
4. Implement `app/routers/macros.py` — all endpoints per spec
5. Register router in `main.py`
6. Write tests in `tests/test_macros.py`:
   - Test today's totals calculation
   - Test percentage calculations
   - Test remaining with various scenarios (under, at, over target)
   - Test history generates snapshots
   - Test history includes body measurements

### Phase 8: Exercises Feature
**Goal**: Log exercises with structured + unstructured data

**Tasks**:
1. Create `app/models/exercise.py`:
   - `ExerciseCreate` — date, exercise_type, duration_minutes, details (dict)
   - `ExerciseResponse` — includes id and created_at
   - `ExerciseUpdate` — all fields optional
2. Implement `app/services/exercise_service.py`:
   - `create_exercise(data)`
   - `get_exercises(date)`
   - `get_exercise_history(days)`
   - `update_exercise(id, data)`
   - `delete_exercise(id)`
3. Implement `app/routers/exercises.py` — all endpoints per spec
4. Register router in `main.py`
5. Write tests in `tests/test_exercises.py`:
   - Test CRUD operations
   - Test JSON details stored and retrieved correctly
   - Test history endpoint

### Phase 9: Admin & Polish
**Goal**: Cleanup operations, error handling, final touches

**Tasks**:
1. Implement `app/routers/admin.py`:
   - `DELETE /admin/clear-foods`
   - `DELETE /admin/clear-exercises`
   - `DELETE /admin/clear-snapshots`
   - `DELETE /admin/clear-body`
   - `DELETE /admin/clear-all`
2. Register router in `main.py`
3. Add global exception handler in `main.py` for consistent error responses
4. Add request logging middleware (optional, for debugging)
5. Ensure all routers are properly registered with tags for OpenAPI docs
6. Write integration tests in `tests/test_integration.py`:
   - Full flow: ingredient → recipe → log → check macros
   - Delete flow: log foods → delete by marker → verify totals change
   - History flow: log multiple days → request history → verify data

### Phase 10: Claude Skill
**Goal**: Skill definition for natural language interaction

**Tasks**:
1. Create `skill/SKILL.md` with:
   - Overview of what the API does
   - Base URL placeholder and auth instructions
   - Endpoint quick reference
   - Example natural language commands and how to translate them:
     - "Log my protein shake for breakfast" → `POST /foods/from-recipe`
     - "What are my macros today?" → `GET /macros/today`
     - "How much protein do I have left?" → `GET /macros/remaining`
     - "I weighed 185 this morning" → `POST /body`
     - "Show me the last week" → `GET /macros/history?days=7`
     - "Delete breakfast_shake from today" → `DELETE /foods/by-marker`
   - Common flows documented
2. Test skill manually with Claude

### Phase 11: Deployment
**Goal**: Running on Railway

**Tasks**:
1. Test locally:
   ```bash
   docker build -t health-tracker .
   docker run -p 8000:8000 -e HEALTH_TRACKER_API_TOKEN=test -e HEALTH_TRACKER_DATABASE_PATH=/data/health.db health-tracker
   ```
2. Create Railway project
3. Add persistent volume mounted at `/data`
4. Set environment variables:
   - `HEALTH_TRACKER_API_TOKEN` — generate a secure token
   - `HEALTH_TRACKER_DATABASE_PATH` — `/data/health.db`
5. Deploy via Railway CLI or GitHub integration
6. Verify all endpoints work
7. Update `skill/SKILL.md` with production URL
8. Document deployment process in `README.md`

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HEALTH_TRACKER_API_TOKEN` | Bearer token for authentication | — | Yes |
| `HEALTH_TRACKER_DATABASE_PATH` | Path to SQLite database file | `./data/health.db` | No |

---

## Claude Skill Example Commands

| Natural Language | API Translation |
|------------------|-----------------|
| "Log my protein shake for breakfast" | `POST /foods/from-recipe` with marker `breakfast_shake` |
| "I had 2 eggs for breakfast" | `POST /foods` with marker `breakfast_eggs` |
| "What are my macros so far today?" | `GET /macros/today` |
| "How much protein do I have left?" | `GET /macros/remaining` → extract protein |
| "How did I do this week?" | `GET /macros/history?days=7` |
| "I weighed 185.5 this morning" | `POST /body` |
| "What's my weight trend?" | `GET /macros/history?days=14` → extract body data |
| "Delete breakfast_shake from today" | `DELETE /foods/by-marker?date=today&marker=breakfast_shake` |
| "I walked 3 miles in 45 minutes" | `POST /exercises` with type `walk` and details |
| "Create a recipe called Overnight Oats" | `POST /recipes` |
| "What recipes do I have?" | `GET /recipes` |
| "Clear everything from today" | `DELETE /foods/clear?date=today` |

---

## Appendix: Default Profile Values

When profile is first accessed, create with these defaults:

```json
{
  "birthdate": null,
  "height_inches": null,
  "calories_min": 1800,
  "calories_max": 2200,
  "protein_min_g": 150,
  "protein_max_g": 180,
  "carbs_min_g": 150,
  "carbs_max_g": 200,
  "fats_min_g": 50,
  "fats_max_g": 70,
  "sodium_max_mg": 2300
}
```

---

## Appendix: SQLite Schema SQL

```sql
-- User profile (single row)
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    birthdate DATE,
    height_inches REAL,
    calories_min INTEGER NOT NULL DEFAULT 1800,
    calories_max INTEGER NOT NULL DEFAULT 2200,
    protein_min_g INTEGER NOT NULL DEFAULT 150,
    protein_max_g INTEGER NOT NULL DEFAULT 180,
    carbs_min_g INTEGER NOT NULL DEFAULT 150,
    carbs_max_g INTEGER NOT NULL DEFAULT 200,
    fats_min_g INTEGER NOT NULL DEFAULT 50,
    fats_max_g INTEGER NOT NULL DEFAULT 70,
    sodium_max_mg INTEGER NOT NULL DEFAULT 2300,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingredients
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    default_amount REAL NOT NULL,
    default_unit TEXT NOT NULL,
    calories INTEGER NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fats_g REAL NOT NULL,
    sodium_mg INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipes
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipe items (junction table)
CREATE TABLE IF NOT EXISTS recipe_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    amount REAL NOT NULL,
    unit TEXT NOT NULL
);

-- Foods (logged entries)
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    marker TEXT NOT NULL,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    calories INTEGER NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fats_g REAL NOT NULL,
    sodium_mg INTEGER NOT NULL DEFAULT 0,
    ingredient_id INTEGER REFERENCES ingredients(id),
    recipe_id INTEGER REFERENCES recipes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_foods_date ON foods(date);
CREATE INDEX IF NOT EXISTS idx_foods_date_marker ON foods(date, marker);

-- Daily snapshots
CREATE TABLE IF NOT EXISTS daily_snapshots (
    date DATE PRIMARY KEY,
    calories INTEGER NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fats_g REAL NOT NULL,
    sodium_mg INTEGER NOT NULL,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Body measurements
CREATE TABLE IF NOT EXISTS body_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    weight_lbs REAL,
    waist_cm REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (weight_lbs IS NOT NULL OR waist_cm IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_body_date ON body_measurements(date);

-- Exercises
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    exercise_type TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    details TEXT, -- JSON stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exercises_date ON exercises(date);
```

---

*End of Specification*
