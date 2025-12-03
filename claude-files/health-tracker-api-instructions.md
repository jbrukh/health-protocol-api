# Health Tracker API Instructions

You have access to a personal health tracking API. When the user asks about logging food, checking macros, recording weight, logging workouts, or managing recipes, use this API.

## API Configuration

Load credentials from `skill/health-tracker-tokens.json` (relative to project root):
```json
{
  "health_api_url": "https://your-api-url.up.railway.app",
  "health_api_token": "your-api-token"
}
```

- **Base URL**: Use value from `health_api_url`
- **Authentication**: Include header `Authorization: Bearer <health_api_token>`
- **Content-Type**: `application/json` for POST/PUT requests

## Quick Actions

| User Says | API Call |
|-----------|----------|
| "Log my protein shake" | POST /foods/from-recipe |
| "I had 2 eggs for breakfast" | POST /foods |
| "What are my macros today?" | GET /macros/today |
| "How much protein do I have left?" | GET /macros/remaining |
| "I weighed 185 this morning" | POST /body |
| "I walked 3 miles" | POST /exercises |
| "What recipes do I have?" | GET /recipes |
| "Delete breakfast from today" | DELETE /foods/by-marker |
| "What supplements should I take?" | GET /supplements/schedule |
| "Add vitamin D to my supplements" | POST /supplements |
| "What phase am I in?" | GET /phases/active |
| "Start a cutting phase" | POST /phases |

## API Endpoints

### Macros (Most Common)

**GET /macros/today** - Today's totals and targets
**GET /macros/remaining** - Remaining macros for today
**GET /macros/history?days=7** - Historical data

### Foods

**POST /foods** - Log food directly
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

**POST /foods/from-recipe** - Log from saved recipe
```json
{
  "recipe_id": 1,
  "date": "2025-01-15",
  "marker": "breakfast_shake",
  "scale": 1.0
}
```

**GET /foods?date=2025-01-15** - Get foods for date
**DELETE /foods/by-marker?date=2025-01-15&marker=breakfast** - Delete by marker
**DELETE /foods/clear?date=2025-01-15** - Clear all for date

### Body Measurements

**POST /body**
```json
{
  "date": "2025-01-15",
  "time": "07:30:00",
  "weight_lbs": 185.5,
  "waist_cm": 86.0
}
```

**GET /body/latest** - Most recent measurement
**GET /body/range?start_date=2025-01-01&end_date=2025-01-15** - Date range

### Exercises

**POST /exercises**
```json
{
  "date": "2025-01-15",
  "exercise_type": "walk",
  "duration_minutes": 45,
  "details": {"miles": 3.2, "active_calories": 280}
}
```
Types: walk, run, bike, swim, strength, yoga, other

**GET /exercises?date=2025-01-15** - Get exercises for date

### Profile

**GET /profile** - Get profile with daily targets
**PUT /profile** - Update targets
```json
{
  "name": "string",
  "daily_calories": 2000,
  "daily_protein_g": 150,
  "daily_carbs_g": 200,
  "daily_fats_g": 65,
  "daily_sodium_mg": 2300
}
```

### Recipes

**GET /recipes** - List all recipes
**GET /recipes/{id}** - Get recipe with totals
**POST /recipes** - Create recipe `{"name": "...", "description": "..."}`
**POST /recipes/{id}/items** - Add ingredient `{"ingredient_id": 1, "quantity": 2.0}`

### Ingredients

**GET /ingredients** - List all
**GET /ingredients/search?q=chicken** - Search by name
**POST /ingredients**
```json
{
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

### Supplements

**POST /supplements** - Create a supplement
```json
{
  "name": "Vitamin D3",
  "dosage": "5000 IU",
  "purpose": "Vitamin D supplementation",
  "time_of_day": "morning",
  "with_food": true,
  "notes": "Take with fatty meal",
  "start_date": "2025-01-15",
  "end_date": null
}
```
- `time_of_day`: morning, midday, afternoon, evening, bedtime

**GET /supplements** - List all supplements
- Query params: `active=true|false`, `time_of_day=morning|midday|afternoon|evening|bedtime`

**GET /supplements/active** - Get currently active supplements
**GET /supplements/schedule** - Today's supplement schedule by time of day
**GET /supplements/history?start_date=2025-01-01&end_date=2025-01-31** - Supplements active during range
**GET /supplements/{id}** - Get single supplement
**PUT /supplements/{id}** - Update supplement
**DELETE /supplements/{id}** - Delete supplement

### Phases

**POST /phases** - Create a health phase
```json
{
  "name": "Cutting Phase",
  "description": "Caloric deficit for fat loss",
  "start_date": "2025-01-15",
  "end_date": "2025-02-15",
  "is_recurring": false,
  "recurrence_interval_days": null
}
```

**GET /phases** - List all phases
- Query params: `active=true|false`, `include_past=true|false`

**GET /phases/active** - Get active phases + upcoming (next 7 days)
- Returns `active_phases` (currently running) and `upcoming_phases` (starting soon)
- Includes `days_remaining` for active, `days_until_start` for upcoming

**GET /phases/{id}** - Get single phase
**PUT /phases/{id}** - Update phase
**DELETE /phases/{id}** - Delete phase

### Admin

**DELETE /admin/clear-supplements** - Clear all supplements
**DELETE /admin/clear-phases** - Clear all phases
**DELETE /admin/clear-all** - Clear everything except profile

## Usage Notes

- Always use today's date in YYYY-MM-DD format unless user specifies otherwise
- Use meaningful markers like "breakfast_eggs", "lunch_salad", "dinner_chicken"
- When logging food, estimate macros if user doesn't provide them
- After logging, offer to check remaining macros
- For supplements, check /supplements/schedule to show the user what to take today
- For phases, use /phases/active to show current protocols and what's coming up
