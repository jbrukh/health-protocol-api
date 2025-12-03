# Health Tracker Claude Skill

This skill allows Claude to interact with a personal health tracking API for food, macro, exercise, and body measurement logging.

## Base URL

Set `HEALTH_API_URL` to your deployed API URL.

## Authentication

All requests require header:
```
Authorization: Bearer <API_TOKEN>
```

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
