# Jake's Health Protocol API

A health tracking API built with FastAPI, designed to serve as a backend for a Custom GPT health advisor. Focused on weight loss tracking with food logging, nutrition labels, recipes, and macro targets.

**Version**: 2.1.0

## Features

- **Food Tracking**: Log food entries with ingredients, track macros (protein, carbs, fat, sodium) and calories
- **Ingredients**: Manage ingredient database with nutrition facts per serving
- **Nutrition Labels**: Store packaged food nutrition labels with barcode support, convert to ingredients
- **Recipes**: Create and log recipes with automatic macro calculation
- **Targets**: Set and track nutritional goals with effective dates
- **Dashboard**: Daily overview with progress tracking against targets

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Testing**: pytest with async support (SQLite in-memory)
- **Deployment**: Railway

## API Documentation

Once deployed, the OpenAPI docs are available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

The API is designed for Custom GPT integration with 22 operations (under the 30 operation limit).

## Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/health_protocol"
export API_KEY="your-secret-key"
export ENVIRONMENT="development"
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## Testing

Run all tests with pytest:
```bash
pytest tests/ -v
```

Tests use SQLite in-memory database and include:
- Unit tests for nutrition calculations and unit conversions
- API tests for all endpoints
- Integration tests for Custom GPT use cases

### Use Case Tests

The test suite includes 5 comprehensive integration tests that simulate real Custom GPT workflows:

1. **Natural Language Food Logging**: User says "I ate two eggs and bread" - GPT creates ingredients, logs food, shows summary
2. **Weekly History for Advice**: GPT queries 7-day macro history to give informed suggestions
3. **Update with Actual Label**: User corrects estimated macros with actual nutrition label data
4. **Favorite Protein Powder**: User saves nutrition label, converts to ingredient, creates shake recipe
5. **Target Updates**: User sets targets, checks progress, updates based on GPT advice

## Deployment to Railway

1. Create a new Railway project
2. Add a PostgreSQL database
3. Connect your repository
4. Set environment variables:
   - `API_KEY`: Your secret API key for Bearer authentication
   - `DATABASE_URL`: Set automatically by Railway (uses `postgresql+asyncpg://`)
   - `OPENAPI_SERVER_URL`: Your Railway deployment URL (optional, for OpenAPI schema)

## Custom GPT Integration

The API generates an OpenAPI 3.0 specification compatible with ChatGPT Custom GPT Actions:

1. Deploy the API to Railway
2. In ChatGPT, create a Custom GPT
3. Add an Action using the OpenAPI schema from `/openapi.json`
4. Configure authentication with Bearer token using your `API_KEY`

## API Endpoints

### Food Tracking
- `POST /api/v1/food` - Log food entry (with ingredient or manual macros)
- `GET /api/v1/food?date={date}` - Get entries for date
- `PATCH /api/v1/food/{id}` - Update food entry
- `DELETE /api/v1/food/{id}` - Delete food entry
- `GET /api/v1/food/summary?date={date}` - Get daily macro summary
- `GET /api/v1/food/history?start={date}&end={date}` - Get multi-day history

### Ingredients
- `POST /api/v1/ingredients` - Create ingredient with nutrition facts
- `GET /api/v1/ingredients` - List all ingredients
- `GET /api/v1/ingredients/{id}` - Get ingredient by ID
- `PUT /api/v1/ingredients/{id}` - Update ingredient
- `DELETE /api/v1/ingredients/{id}` - Delete ingredient
- `GET /api/v1/ingredients/search?q={query}` - Search ingredients by name
- `POST /api/v1/ingredients/{id}/set-default` - Mark as default ingredient

### Nutrition Labels
- `POST /api/v1/nutrition-labels` - Store nutrition label (with optional barcode)
- `GET /api/v1/nutrition-labels` - List all labels
- `GET /api/v1/nutrition-labels/{id}` - Get label by ID
- `GET /api/v1/nutrition-labels/barcode/{barcode}` - Look up by barcode
- `POST /api/v1/nutrition-labels/{id}/to-ingredient` - Convert label to ingredient

### Recipes
- `POST /api/v1/recipes` - Create recipe with ingredients
- `GET /api/v1/recipes` - List all recipes
- `GET /api/v1/recipes/{id}` - Get recipe with calculated macros
- `POST /api/v1/recipes/{id}/log?date={date}&servings={n}` - Log recipe as food entry

### Targets
- `POST /api/v1/targets` - Set nutritional target (with effective date)
- `GET /api/v1/targets` - Get current active targets

### Dashboard
- `GET /api/v1/dashboard?date={date}` - Daily overview with:
  - Food summary (totals for all macros)
  - Food entries list
  - Target progress (current vs target, percent complete)

### Admin (Hidden from OpenAPI)
- `POST /api/v1/admin/clear` - Clear all tables or specific table
- `POST /api/v1/admin/clear?table={name}` - Clear specific table

## Database Schema

### Tables
- `ingredients` - Base nutrition facts per serving
- `food_entries` - Daily food log entries
- `daily_logs` - Daily log containers (one per date)
- `recipes` - Saved recipes
- `recipe_ingredients` - Recipe ingredient associations
- `targets` - Nutritional targets with effective dates
- `nutrition_labels` - Packaged food labels with barcode

## License

Private repository - All rights reserved.
