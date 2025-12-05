# Health Tracker API

A lightweight Python/FastAPI REST API for single-user food, macro, exercise, and body measurement tracking.

## Features

- Track foods, macros, and calories against configurable targets
- Save reusable ingredients and recipes (recipes expand to individual food entries)
- Log exercises with structured + unstructured data
- Track daily weight and waist measurements
- Query today's progress, remaining budget, and historical trends

## Quick Start

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export HEALTH_TRACKER_API_TOKEN=your-token-here
export HEALTH_TRACKER_DATABASE_PATH=./data/health.db
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

5. Access the API at `http://localhost:8000`
6. View API docs at `http://localhost:8000/docs`

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

### Docker

Build and run:
```bash
docker build -t health-tracker .
docker run -p 8000:8000 -e HEALTH_TRACKER_API_TOKEN=your-token -v $(pwd)/data:/data health-tracker
```

## API Authentication

All endpoints (except `/health`) require a Bearer token:

```
Authorization: Bearer <HEALTH_TRACKER_API_TOKEN>
```

## API Endpoints

### Profile
- `GET /profile` - Get user profile with targets
- `PUT /profile` - Update profile

### Ingredients
- `POST /ingredients` - Create ingredient
- `GET /ingredients` - List all ingredients
- `GET /ingredients/search?q=query` - Search ingredients
- `GET /ingredients/{id}` - Get ingredient
- `PUT /ingredients/{id}` - Update ingredient
- `DELETE /ingredients/{id}` - Delete ingredient

### Recipes
- `POST /recipes` - Create recipe with items
- `GET /recipes` - List all recipes
- `GET /recipes/{id}` - Get recipe with items and totals
- `PUT /recipes/{id}` - Update recipe name
- `POST /recipes/{id}/items` - Add item to recipe
- `PUT /recipes/{id}/items/{item_id}` - Update recipe item
- `DELETE /recipes/{id}/items/{item_id}` - Remove recipe item
- `DELETE /recipes/{id}` - Delete recipe

### Foods
- `POST /foods` - Log food entry
- `POST /foods/from-recipe` - Log foods from recipe
- `GET /foods?date=YYYY-MM-DD` - Get foods for date
- `GET /foods?date=YYYY-MM-DD&marker=breakfast` - Filter by marker
- `PUT /foods/{id}` - Update food entry
- `DELETE /foods/{id}` - Delete food entry
- `DELETE /foods/by-marker?date=YYYY-MM-DD&marker=breakfast` - Delete by marker
- `DELETE /foods/clear?date=YYYY-MM-DD` - Clear all foods for date

### Macros
- `GET /macros/today` - Today's totals with target percentages
- `GET /macros/remaining` - Remaining budget for today
- `GET /macros/history?days=7` - Historical data with body measurements

### Body Measurements
- `POST /body` - Log measurement
- `GET /body?date=YYYY-MM-DD` - Get measurements for date
- `GET /body/latest` - Get most recent measurement
- `PUT /body/{id}` - Update measurement
- `DELETE /body/{id}` - Delete measurement

### Exercises
- `POST /exercises` - Log exercise
- `GET /exercises?date=YYYY-MM-DD` - Get exercises for date
- `GET /exercises/history?days=7` - Exercise history
- `PUT /exercises/{id}` - Update exercise
- `DELETE /exercises/{id}` - Delete exercise

### Admin
- `DELETE /admin/clear-foods` - Clear all foods
- `DELETE /admin/clear-exercises` - Clear all exercises
- `DELETE /admin/clear-snapshots` - Clear all snapshots
- `DELETE /admin/clear-body` - Clear all body measurements
- `DELETE /admin/clear-all` - Clear everything except profile

### Health
- `GET /health` - Health check (no auth required)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HEALTH_TRACKER_API_TOKEN` | Bearer token for authentication | Required |
| `HEALTH_TRACKER_DATABASE_PATH` | Path to SQLite database | `./data/health.db` |

## Deployment on Railway

1. Connect your GitHub repository to Railway
2. Add a persistent volume mounted at `/data`
3. Set environment variables:
   - `HEALTH_TRACKER_API_TOKEN` - Generate a secure token
   - `HEALTH_TRACKER_DATABASE_PATH` - `/data/health.db`
4. Deploy!
