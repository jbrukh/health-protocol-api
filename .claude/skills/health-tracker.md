---
name: health-tracker
description: Track daily food intake, macros, body measurements, and exercises via a personal health API. Use when the user wants to log meals, check macro progress, record weight, log workouts, manage recipes/ingredients, or review health trends.
---

# Health Tracker Skill

This skill allows you to interact with a personal health tracking API for food, macro, exercise, and body measurement logging.

## Configuration Required

Before using this skill, ensure these environment variables are set:
- `HEALTH_API_URL`: Your deployed API URL (e.g., `https://health-tracker-api-production.up.railway.app`)
- `HEALTH_API_TOKEN`: Your API authentication token

## Making API Requests

All requests to the Health Tracker API must:
1. Use the base URL from `HEALTH_API_URL`
2. Include the Authorization header: `Authorization: Bearer <HEALTH_API_TOKEN>`
3. Use JSON content type for POST/PUT requests

## Quick Reference

### Logging Food

**Direct entry:**
```
POST /foods
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

**From recipe:**
```
POST /foods/from-recipe
{
  "recipe_id": 1,
  "date": "2025-01-15",
  "marker": "breakfast_shake",
  "scale": 1.0
}
```

### Checking Macros

**Today's progress:**
```
GET /macros/today
```

**Remaining budget:**
```
GET /macros/remaining
```

**History:**
```
GET /macros/history?days=7
```

### Body Measurements

**Log weight/waist:**
```
POST /body
{
  "date": "2025-01-15",
  "time": "07:30:00",
  "weight_lbs": 185.5,
  "waist_cm": 86.0
}
```

### Exercises

**Log exercise:**
```
POST /exercises
{
  "date": "2025-01-15",
  "exercise_type": "walk",
  "duration_minutes": 45,
  "details": {
    "miles": 3.2,
    "active_calories": 280
  }
}
```

## Natural Language Translations

| User Says | API Call |
|-----------|----------|
| "Log my protein shake for breakfast" | `POST /foods/from-recipe` with marker `breakfast_shake` |
| "I had 2 eggs for breakfast" | `POST /foods` with marker `breakfast_eggs` |
| "What are my macros so far today?" | `GET /macros/today` |
| "How much protein do I have left?" | `GET /macros/remaining` → extract protein |
| "How did I do this week?" | `GET /macros/history?days=7` |
| "I weighed 185.5 this morning" | `POST /body` |
| "What's my weight trend?" | `GET /macros/history?days=14` → extract body data |
| "Delete breakfast_shake from today" | `DELETE /foods/by-marker?date=today&marker=breakfast_shake` |
| "I walked 3 miles in 45 minutes" | `POST /exercises` with type `walk` |
| "Create a recipe called Overnight Oats" | `POST /recipes` |
| "What recipes do I have?" | `GET /recipes` |
| "Clear everything from today" | `DELETE /foods/clear?date=today` |

## Common Flows

### Morning Routine
1. Log weight: `POST /body`
2. Log breakfast from recipe: `POST /foods/from-recipe`
3. Check remaining macros: `GET /macros/remaining`

### End of Day Review
1. Check today's totals: `GET /macros/today`
2. Review weekly trend: `GET /macros/history?days=7`

### Creating New Foods
1. Search for similar ingredient: `GET /ingredients/search?q=chicken`
2. If not found, create: `POST /ingredients`
3. Optionally add to recipe: `POST /recipes/{id}/items`

---

## Complete API Reference

### Profile Endpoints

**GET /profile** - Get user profile with daily macro targets
```json
Response: {
  "id": 1,
  "name": "string",
  "birthdate": "2000-01-15",
  "daily_calories": 2000,
  "daily_protein_g": 150,
  "daily_carbs_g": 200,
  "daily_fats_g": 65,
  "daily_sodium_mg": 2300
}
```

**PUT /profile** - Update profile (all fields optional)
```json
Request: {
  "name": "string",
  "birthdate": "2000-01-15",
  "daily_calories": 2000,
  "daily_protein_g": 150,
  "daily_carbs_g": 200,
  "daily_fats_g": 65,
  "daily_sodium_mg": 2300
}
```

### Ingredient Endpoints

**GET /ingredients** - List all ingredients
**GET /ingredients/{id}** - Get ingredient by ID
**GET /ingredients/search?q={query}** - Search ingredients by name

**POST /ingredients** - Create ingredient
```json
Request: {
  "name": "Chicken Breast",
  "serving_size": 100,
  "serving_unit": "g",
  "calories": 165,
  "protein_g": 31,
  "carbs_g": 0,
  "fats_g": 3.6,
  "sodium_mg": 74
}
```

**PUT /ingredients/{id}** - Update ingredient (all fields optional)
**DELETE /ingredients/{id}** - Delete ingredient

### Recipe Endpoints

**GET /recipes** - List all recipes
**GET /recipes/{id}** - Get recipe with calculated totals

**POST /recipes** - Create recipe
```json
Request: {
  "name": "Protein Shake",
  "description": "Post-workout shake"
}
```

**PUT /recipes/{id}** - Update recipe name/description
**DELETE /recipes/{id}** - Delete recipe

**POST /recipes/{id}/items** - Add ingredient to recipe
```json
Request: {
  "ingredient_id": 1,
  "quantity": 2.0
}
```

**PUT /recipes/{id}/items/{item_id}** - Update recipe item quantity
**DELETE /recipes/{id}/items/{item_id}** - Remove item from recipe

### Food Endpoints

**GET /foods?date={YYYY-MM-DD}&marker={optional}** - Get foods for date

**POST /foods** - Log food directly
```json
Request: {
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

**POST /foods/from-recipe** - Log foods from recipe
```json
Request: {
  "recipe_id": 1,
  "date": "2025-01-15",
  "marker": "breakfast_shake",
  "scale": 1.0
}
```

**GET /foods/{id}** - Get food by ID
**PUT /foods/{id}** - Update food entry
**DELETE /foods/{id}** - Delete food entry
**DELETE /foods/by-marker?date={YYYY-MM-DD}&marker={marker}** - Delete foods by marker
**DELETE /foods/clear?date={YYYY-MM-DD}** - Clear all foods for date

### Body Measurement Endpoints

**GET /body?date={YYYY-MM-DD}** - Get measurements for date
**GET /body/latest** - Get most recent measurement
**GET /body/range?start_date={}&end_date={}** - Get measurements in range

**POST /body** - Log body measurement
```json
Request: {
  "date": "2025-01-15",
  "time": "07:30:00",
  "weight_lbs": 185.5,
  "waist_cm": 86.0
}
```

**DELETE /body/{id}** - Delete measurement

### Exercise Endpoints

**GET /exercises?date={YYYY-MM-DD}** - Get exercises for date
**GET /exercises/range?start_date={}&end_date={}** - Get exercises in range

**POST /exercises** - Log exercise
```json
Request: {
  "date": "2025-01-15",
  "exercise_type": "walk",
  "duration_minutes": 45,
  "details": {
    "miles": 3.2,
    "active_calories": 280
  }
}
```
Exercise types: walk, run, bike, swim, strength, yoga, other

**PUT /exercises/{id}** - Update exercise
**DELETE /exercises/{id}** - Delete exercise

### Macro Endpoints

**GET /macros/today** - Get today's macro totals and targets
```json
Response: {
  "date": "2025-01-15",
  "consumed": {"calories": 800, "protein_g": 60, ...},
  "targets": {"calories": 2000, "protein_g": 150, ...},
  "body": {"weight_lbs": 185.5, "waist_cm": 86.0}
}
```

**GET /macros/remaining** - Get remaining macros for today
```json
Response: {
  "date": "2025-01-15",
  "remaining": {"calories": 1200, "protein_g": 90, ...},
  "percentage_consumed": {"calories": 40, "protein_g": 40, ...}
}
```

**GET /macros/history?days={n}** - Get macro history
```json
Response: [
  {
    "date": "2025-01-15",
    "consumed": {...},
    "targets": {...},
    "body": {...},
    "exercises": [...]
  }
]
```

**GET /macros/snapshot?date={YYYY-MM-DD}** - Get snapshot for specific date

### Admin Endpoints

**POST /admin/reset** - Reset all data (profile, ingredients, recipes, foods, body, exercises)
