# Health Tracker API - Complete Reference

A lightweight REST API for comprehensive health and fitness tracking including food/macro logging, body measurements, exercise tracking, supplement management, and Withings device integration.

**Base URL**: `https://health-tracker-api.up.railway.app` (production) or `https://health-tracker-api-staging.up.railway.app` (staging)

## Authentication

All endpoints (except `/health` and Withings OAuth callbacks) require Bearer token authentication.

```
Authorization: Bearer <API_TOKEN>
```

---

## API Endpoints Overview

### Profile Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Get user profile with computed age |
| PUT | `/profile` | Update user profile and targets |

### Ingredients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ingredients` | List all ingredients |
| POST | `/ingredients` | Create a new ingredient |
| GET | `/ingredients/search?q=` | Search ingredients by name |
| GET | `/ingredients/{id}` | Get ingredient by ID |
| PUT | `/ingredients/{id}` | Update an ingredient |
| DELETE | `/ingredients/{id}` | Delete an ingredient |

### Recipes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recipes` | List all recipes with computed totals |
| POST | `/recipes` | Create a recipe with items |
| GET | `/recipes/{id}` | Get recipe by ID with items and totals |
| PUT | `/recipes/{id}` | Update recipe name |
| DELETE | `/recipes/{id}` | Delete a recipe |
| POST | `/recipes/{id}/items` | Add an item to a recipe |
| PUT | `/recipes/{id}/items/{item_id}` | Update a recipe item |
| DELETE | `/recipes/{id}/items/{item_id}` | Remove item from recipe |

### Foods (Daily Food Log)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/foods` | Log a food entry |
| GET | `/foods?date=YYYY-MM-DD` | Get food entries for a date |
| POST | `/foods/from-recipe` | Log foods from a recipe |
| DELETE | `/foods/by-marker?date=&marker=` | Delete foods by marker |
| DELETE | `/foods/clear?date=` | Clear all foods for a date |
| GET | `/foods/{id}` | Get food entry by ID |
| PUT | `/foods/{id}` | Update a food entry |
| DELETE | `/foods/{id}` | Delete a food entry |

### Macros (Daily Nutrition Summary)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/macros/today` | Get today's macro totals with target percentages |
| GET | `/macros/remaining` | Get remaining macro budget for today |
| GET | `/macros/history` | Get macro history (date range, pagination) |

### Body Measurements
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/body` | Log a body measurement |
| GET | `/body` | Get measurements (date range, pagination) |
| GET | `/body/summary` | Get data summary (date range, total count) |
| GET | `/body/latest` | Get most recent measurement |
| GET | `/body/{id}` | Get measurement by ID |
| PUT | `/body/{id}` | Update a measurement |
| DELETE | `/body/{id}` | Delete a measurement |

### Exercises
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/exercises` | Log an exercise |
| GET | `/exercises?date=YYYY-MM-DD` | Get exercises for a date |
| GET | `/exercises/history?days=7` | Get exercise history |
| GET | `/exercises/{id}` | Get exercise by ID |
| PUT | `/exercises/{id}` | Update an exercise |
| DELETE | `/exercises/{id}` | Delete an exercise |

### Supplements
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/supplements` | Create a supplement entry |
| GET | `/supplements` | List supplements (filter by active/time_of_day) |
| GET | `/supplements/active` | Get currently active supplements |
| GET | `/supplements/schedule` | Get today's supplement schedule by time |
| GET | `/supplements/history?start_date=&end_date=` | Get supplement history for date range |
| GET | `/supplements/{id}` | Get supplement by ID |
| PUT | `/supplements/{id}` | Update a supplement |
| DELETE | `/supplements/{id}` | Delete a supplement |

### Phases (Life/Training Phases)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/phases` | Create a phase |
| GET | `/phases` | List all phases |
| GET | `/phases/active` | Get active and upcoming phases |
| GET | `/phases/{id}` | Get phase by ID |
| PUT | `/phases/{id}` | Update a phase |
| DELETE | `/phases/{id}` | Delete a phase |

### Blood Pressure
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/blood-pressure` | Get readings (date range, pagination) |
| GET | `/blood-pressure/summary` | Get data summary (date range, total count) |
| GET | `/blood-pressure/latest` | Get most recent reading |

*Note: Blood pressure data is synced from Withings. Manual entry not supported.*

### Daily Activity (Steps, Distance, etc.)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/activity` | Get activity (date range, pagination) |
| GET | `/activity/summary` | Get data summary (date range, total count) |
| GET | `/activity/latest` | Get most recent activity |

*Note: Activity data is synced from Withings. Manual entry not supported.*

### Sleep
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sleep?date=YYYY-MM-DD` | Get sleep data for a date (default: today) |
| GET | `/sleep/latest` | Get most recent sleep entry |

*Note: Sleep data is synced from Withings. Manual entry not supported.*

### Withings Integration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/withings/auth` | Get Withings OAuth authorization URL |
| GET | `/withings/callback` | OAuth callback (no auth required) |
| GET | `/withings/status` | Check Withings connection status |
| POST | `/withings/refresh` | Force token refresh |
| DELETE | `/withings/disconnect` | Disconnect Withings integration |
| POST | `/withings/webhook` | Receive webhook notifications (no auth) |
| POST | `/withings/backfill` | Manual historical data backfill |

---

## Data Models

### Profile

**ProfileResponse**
```json
{
  "birthdate": "1990-01-15",
  "age": 34,
  "height_inches": 70.5,
  "targets": {
    "calories_min": 1800,
    "calories_max": 2200,
    "protein_min_g": 150,
    "protein_max_g": 200,
    "carbs_min_g": 150,
    "carbs_max_g": 250,
    "fats_min_g": 50,
    "fats_max_g": 80,
    "sodium_max_mg": 2300
  },
  "updated_at": "2024-01-15T10:30:00"
}
```

**ProfileUpdate** (all fields optional)
```json
{
  "birthdate": "1990-01-15",
  "height_inches": 70.5,
  "calories_min": 1800,
  "calories_max": 2200,
  "protein_min_g": 150,
  "protein_max_g": 200,
  "carbs_min_g": 150,
  "carbs_max_g": 250,
  "fats_min_g": 50,
  "fats_max_g": 80,
  "sodium_max_mg": 2300
}
```

### Ingredients

**IngredientCreate**
```json
{
  "name": "Chicken Breast",
  "default_amount": 4,
  "default_unit": "oz",
  "calories": 140,
  "protein_g": 26,
  "carbs_g": 0,
  "fats_g": 3,
  "sodium_mg": 70
}
```

**IngredientResponse**
```json
{
  "id": 1,
  "name": "Chicken Breast",
  "default_amount": 4,
  "default_unit": "oz",
  "calories": 140,
  "protein_g": 26,
  "carbs_g": 0,
  "fats_g": 3,
  "sodium_mg": 70,
  "created_at": "2024-01-15T10:30:00"
}
```

### Recipes

**RecipeCreate**
```json
{
  "name": "Protein Bowl",
  "items": [
    {"ingredient_id": 1, "amount": 6, "unit": "oz"},
    {"ingredient_id": 2, "amount": 1, "unit": "cup"}
  ]
}
```

**RecipeResponse**
```json
{
  "id": 1,
  "name": "Protein Bowl",
  "items": [
    {
      "id": 1,
      "ingredient_id": 1,
      "ingredient_name": "Chicken Breast",
      "amount": 6,
      "unit": "oz",
      "calories": 210,
      "protein_g": 39,
      "carbs_g": 0,
      "fats_g": 4.5,
      "sodium_mg": 105
    }
  ],
  "totals": {
    "calories": 450,
    "protein_g": 52,
    "carbs_g": 30,
    "fats_g": 10,
    "sodium_mg": 200
  },
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Foods

**FoodCreate**
```json
{
  "date": "2024-01-15",
  "marker": "breakfast",
  "name": "Scrambled Eggs",
  "amount": 3,
  "unit": "eggs",
  "calories": 210,
  "protein_g": 18,
  "carbs_g": 1,
  "fats_g": 15,
  "sodium_mg": 300
}
```

**FoodFromRecipe** (logs all recipe items as individual food entries)
```json
{
  "recipe_id": 1,
  "date": "2024-01-15",
  "marker": "lunch",
  "scale": 1.0
}
```

**FoodResponse**
```json
{
  "id": 1,
  "date": "2024-01-15",
  "marker": "breakfast",
  "name": "Scrambled Eggs",
  "amount": 3,
  "unit": "eggs",
  "calories": 210,
  "protein_g": 18,
  "carbs_g": 1,
  "fats_g": 15,
  "sodium_mg": 300,
  "ingredient_id": null,
  "recipe_id": null,
  "created_at": "2024-01-15T08:00:00"
}
```

### Macros

**MacroTodayResponse**
```json
{
  "date": "2024-01-15",
  "totals": {
    "calories": 1500,
    "protein_g": 120,
    "carbs_g": 150,
    "fats_g": 50,
    "sodium_mg": 1800
  },
  "targets": {
    "calories": {"min": 1800, "max": 2200, "current": 1500, "percent_of_min": 83.3, "percent_of_max": 68.2},
    "protein_g": {"min": 150, "max": 200, "current": 120, "percent_of_min": 80.0, "percent_of_max": 60.0},
    "carbs_g": {"min": 150, "max": 250, "current": 150, "percent_of_min": 100.0, "percent_of_max": 60.0},
    "fats_g": {"min": 50, "max": 80, "current": 50, "percent_of_min": 100.0, "percent_of_max": 62.5},
    "sodium_mg": {"max": 2300, "current": 1800, "percent_of_max": 78.3}
  }
}
```

**MacroRemainingResponse**
```json
{
  "date": "2024-01-15",
  "remaining": {
    "calories": {"min": 300, "max": 700, "note": null},
    "protein_g": {"min": 30, "max": 80, "note": null},
    "carbs_g": {"min": 0, "max": 100, "note": "minimum met"},
    "fats_g": {"min": 0, "max": 30, "note": "minimum met"},
    "sodium_mg": {"max": 500}
  },
  "suggestion": "You have room for 300-700 more calories"
}
```

**MacroHistoryResponse**
```json
{
  "days": [
    {
      "date": "2024-01-15",
      "macros": {
        "calories": 1800,
        "protein_g": 150,
        "carbs_g": 200,
        "fats_g": 60,
        "sodium_mg": 2000
      },
      "body": {
        "weight_lbs": 175.5,
        "waist_cm": 85.0,
        "measurements": [
          {"time": "07:30:00", "weight_lbs": 175.5, "waist_cm": 85.0}
        ]
      }
    }
  ],
  "start_date": "2024-01-08",
  "end_date": "2024-01-15",
  "total_days": 8,
  "limit": 100,
  "offset": 0
}
```

### Body Measurements

**BodyMeasurementCreate**
```json
{
  "date": "2024-01-15",
  "time": "07:30:00",
  "weight_lbs": 175.5,
  "waist_cm": 85.0,
  "fat_mass_lbs": 28.0,
  "muscle_mass_lbs": 140.0,
  "bone_mass_lbs": 7.5,
  "body_water_pct": 55.0,
  "source": "withings"
}
```

Note: At least one of `weight_lbs` or `waist_cm` must be provided.

**BodyMeasurementResponse**
```json
{
  "id": 1,
  "date": "2024-01-15",
  "time": "07:30:00",
  "weight_lbs": 175.5,
  "waist_cm": 85.0,
  "fat_mass_lbs": 28.0,
  "muscle_mass_lbs": 140.0,
  "bone_mass_lbs": 7.5,
  "body_water_pct": 55.0,
  "source": "withings",
  "created_at": "2024-01-15T07:30:00"
}
```

### Exercises

**ExerciseCreate**
```json
{
  "date": "2024-01-15",
  "exercise_type": "strength training",
  "duration_minutes": 60,
  "details": {
    "exercises": ["bench press", "squats", "deadlifts"],
    "sets": 15,
    "notes": "Heavy day"
  }
}
```

**ExerciseResponse**
```json
{
  "id": 1,
  "date": "2024-01-15",
  "exercise_type": "strength training",
  "duration_minutes": 60,
  "details": {"exercises": ["bench press", "squats", "deadlifts"]},
  "created_at": "2024-01-15T18:00:00"
}
```

### Supplements

**TimeOfDay enum values**: `morning`, `midday`, `afternoon`, `evening`, `bedtime`

**SupplementCreate**
```json
{
  "name": "Vitamin D3",
  "dosage_amount": 5000,
  "dosage_unit": "IU",
  "purpose": "Immune support, bone health",
  "time_of_day": "morning",
  "with_food": true,
  "notes": "Take with breakfast",
  "start_date": "2024-01-01",
  "end_date": null
}
```

**SupplementResponse**
```json
{
  "id": 1,
  "name": "Vitamin D3",
  "dosage_amount": 5000,
  "dosage_unit": "IU",
  "dosage_display": "5K IU",
  "purpose": "Immune support, bone health",
  "time_of_day": "morning",
  "with_food": true,
  "notes": "Take with breakfast",
  "start_date": "2024-01-01",
  "end_date": null,
  "is_active": true,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

**SupplementScheduleResponse**
```json
{
  "date": "2024-01-15",
  "schedule": {
    "morning": [
      {"id": 1, "name": "Vitamin D3", "dosage_amount": 5000, "dosage_unit": "IU", "dosage_display": "5K IU", "with_food": true, "notes": null}
    ],
    "evening": [
      {"id": 2, "name": "Magnesium", "dosage_amount": 400, "dosage_unit": "mg", "dosage_display": "400 mg", "with_food": false, "notes": null}
    ]
  },
  "summary": {
    "total_supplements": 2,
    "with_food_count": 1,
    "without_food_count": 1
  }
}
```

### Phases

**PhaseCreate**
```json
{
  "name": "Cut Phase",
  "description": "Caloric deficit for fat loss",
  "start_date": "2024-01-15",
  "end_date": "2024-03-15",
  "is_recurring": false,
  "recurrence_interval_days": null
}
```

**PhaseResponse**
```json
{
  "id": 1,
  "name": "Cut Phase",
  "description": "Caloric deficit for fat loss",
  "start_date": "2024-01-15",
  "end_date": "2024-03-15",
  "is_recurring": false,
  "recurrence_interval_days": null,
  "is_active": true,
  "days_remaining": 45,
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

**ActivePhasesResponse**
```json
{
  "date": "2024-01-15",
  "active_phases": [
    {"id": 1, "name": "Cut Phase", "description": "...", "start_date": "2024-01-15", "end_date": "2024-03-15", "days_remaining": 45, "is_recurring": false}
  ],
  "upcoming_phases": [
    {"id": 2, "name": "Bulk Phase", "description": "...", "start_date": "2024-03-16", "end_date": "2024-06-16", "days_until_start": 60}
  ],
  "total_active": 1,
  "total_upcoming": 1
}
```

### Blood Pressure

*Data synced from Withings - read-only*

**BloodPressureResponse**
```json
{
  "id": 1,
  "date": "2024-01-15",
  "time": "08:00:00",
  "systolic": 120,
  "diastolic": 80,
  "heart_rate": 72,
  "source": "withings",
  "created_at": "2024-01-15T08:00:00"
}
```

**BloodPressureListResponse**
```json
{
  "readings": [...],
  "total_in_range": 50,
  "limit": 100,
  "offset": 0
}
```

**BloodPressureSummaryResponse**
```json
{
  "earliest_date": "2020-01-15",
  "latest_date": "2024-12-07",
  "total_count": 385
}
```

### Daily Activity

*Data synced from Withings - read-only*

**DailyActivityResponse**
```json
{
  "id": 1,
  "date": "2024-01-15",
  "steps": 10000,
  "distance_miles": 4.5,
  "active_calories": 350,
  "elevation_ft": 250,
  "source": "withings",
  "created_at": "2024-01-15T23:59:00",
  "updated_at": "2024-01-15T23:59:00"
}
```

**DailyActivityListResponse**
```json
{
  "activities": [...],
  "total_in_range": 30,
  "limit": 100,
  "offset": 0
}
```

**DailyActivitySummaryResponse**
```json
{
  "earliest_date": "2020-01-15",
  "latest_date": "2024-12-07",
  "total_count": 1825
}
```

### Sleep

*Data synced from Withings - read-only*

**SleepResponse**
```json
{
  "id": 1,
  "date": "2024-01-15",
  "sleep_start": "2024-01-15T23:00:00",
  "sleep_end": "2024-01-16T07:00:00",
  "duration_minutes": 480,
  "deep_minutes": 90,
  "light_minutes": 240,
  "rem_minutes": 120,
  "awake_minutes": 30,
  "source": "withings",
  "created_at": "2024-01-16T07:30:00"
}
```

### Withings Integration

**WithingsStatusResponse**
```json
{
  "connected": true,
  "status": "active",
  "withings_user_id": "12345678",
  "expires_at": "2024-01-22T10:00:00",
  "expires_in_seconds": 604800,
  "subscriptions": [1, 4, 16, 44]
}
```

Subscription appli codes:
- `1`: Weight/Body measurements
- `4`: Blood Pressure
- `16`: Activity
- `44`: Sleep

**WithingsBackfillRequest**
```json
{
  "start_date": "2020-01-01",
  "end_date": "2024-01-15"
}
```

**WithingsBackfillResponse**
```json
{
  "message": "Backfill completed",
  "counts": {
    "body": 1500,
    "blood_pressure": 385,
    "activity": 1825
  }
}
```

---

## Common Patterns

### Date Formats
- All dates use ISO 8601 format: `YYYY-MM-DD`
- All times use 24-hour format: `HH:MM:SS`
- All datetimes use ISO 8601: `YYYY-MM-DDTHH:MM:SS`

### Markers for Food Entries
Common markers used to organize food entries by meal:
- `breakfast`
- `lunch`
- `dinner`
- `snack`
- `pre-workout`
- `post-workout`

### Error Responses
```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- `200`: Success
- `201`: Created
- `204`: No Content (successful delete)
- `400`: Bad Request
- `401`: Unauthorized (missing/invalid token)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## Query Parameters Reference

### Pagination and Date Range Endpoints

The following endpoints support date range filtering and pagination:

#### Body Measurements: `GET /body`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | 30 days ago | Start of date range (YYYY-MM-DD) |
| `end_date` | date | today | End of date range (YYYY-MM-DD) |
| `limit` | int | 100 | Max results (1-1000) |
| `offset` | int | 0 | Number of results to skip |

Example: `GET /body?start_date=2024-01-01&end_date=2024-01-31&limit=50&offset=0`

#### Body Measurements Summary: `GET /body/summary`
No parameters. Returns earliest/latest dates and total count.

#### Blood Pressure: `GET /blood-pressure`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | 30 days ago | Start of date range (YYYY-MM-DD) |
| `end_date` | date | today | End of date range (YYYY-MM-DD) |
| `limit` | int | 100 | Max results (1-1000) |
| `offset` | int | 0 | Number of results to skip |

Example: `GET /blood-pressure?start_date=2024-01-01&end_date=2024-12-31&limit=100`

#### Blood Pressure Summary: `GET /blood-pressure/summary`
No parameters. Returns earliest/latest dates and total count.

#### Activity: `GET /activity`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | 30 days ago | Start of date range (YYYY-MM-DD) |
| `end_date` | date | today | End of date range (YYYY-MM-DD) |
| `limit` | int | 100 | Max results (1-1000) |
| `offset` | int | 0 | Number of results to skip |

Example: `GET /activity?start_date=2024-06-01&end_date=2024-06-30&limit=30`

#### Activity Summary: `GET /activity/summary`
No parameters. Returns earliest/latest dates and total count.

#### Macros History: `GET /macros/history`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | 30 days ago | Start of date range (YYYY-MM-DD) |
| `end_date` | date | today | End of date range (YYYY-MM-DD) |
| `limit` | int | 100 | Max days to return (1-1000) |
| `offset` | int | 0 | Number of days to skip |

Example: `GET /macros/history?start_date=2024-12-01&end_date=2024-12-07&limit=7`

Response includes `total_days`, `limit`, and `offset` for pagination metadata.

### Other Filtered Endpoints

#### Foods: `GET /foods`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | date | today | Date to get entries for (YYYY-MM-DD) |

Example: `GET /foods?date=2024-01-15`

#### Ingredients Search: `GET /ingredients/search`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query (name contains) |

Example: `GET /ingredients/search?q=chicken`

#### Exercises: `GET /exercises`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | date | today | Date to get entries for (YYYY-MM-DD) |

Example: `GET /exercises?date=2024-01-15`

#### Exercises History: `GET /exercises/history`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Number of days of history |

Example: `GET /exercises/history?days=7`

#### Supplements List: `GET /supplements`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | bool | false | Only return active supplements |
| `time_of_day` | string | none | Filter by time (morning, midday, afternoon, evening, bedtime) |

Example: `GET /supplements?active_only=true&time_of_day=morning`

#### Supplements History: `GET /supplements/history`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | required | Start of date range (YYYY-MM-DD) |
| `end_date` | date | required | End of date range (YYYY-MM-DD) |

Example: `GET /supplements/history?start_date=2024-01-01&end_date=2024-01-31`

#### Sleep: `GET /sleep`
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | date | today | Date to get sleep data for (YYYY-MM-DD) |

Example: `GET /sleep?date=2024-01-15`

---

## Usage Examples

### Log breakfast and check remaining macros
1. `POST /foods` with breakfast items
2. `GET /macros/remaining` to see budget for rest of day

### Track a workout
1. `POST /exercises` with exercise details
2. Optionally log post-workout nutrition via `POST /foods`

### Weekly review
1. `GET /macros/history?limit=7` for last 7 days of nutrition
2. `GET /exercises/history?days=7` for workout summary
3. `GET /body/latest` for current measurements

### Get full data history with pagination
```bash
# Get all body measurements in batches of 100
GET /body?start_date=2020-01-01&end_date=2024-12-31&limit=100&offset=0
GET /body?start_date=2020-01-01&end_date=2024-12-31&limit=100&offset=100
# ... continue until all data retrieved

# Check how much data exists first
GET /body/summary
# Returns: {"earliest_date": "2020-01-15", "latest_date": "2024-12-07", "total_count": 1500}
```

### Withings sync
1. `GET /withings/auth` to get OAuth URL
2. User authorizes, redirected to callback
3. System automatically backfills historical data
4. Webhooks receive real-time updates
5. `POST /withings/backfill` for manual re-sync if needed
