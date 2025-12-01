# Jake's Health Protocol API

A health tracking API built with FastAPI, designed to serve as a backend for a Custom GPT health advisor.

## Features

- **Food Tracking**: Log food entries with ingredients, track macros and calories
- **Ingredients**: Manage ingredient database with nutrition facts
- **Recipes**: Create and log recipes with automatic macro calculation
- **Supplements**: Track active supplements with dosage and timing
- **Biomarkers**: Record and compare biomarker readings over time
- **Exercise**: Log exercises with flexible metadata
- **Targets**: Set and track nutritional goals
- **Dashboard**: Daily overview with progress tracking

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Deployment**: Railway

## API Documentation

Once deployed, the OpenAPI docs are available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

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

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## Deployment to Railway

1. Create a new Railway project
2. Add a PostgreSQL database
3. Connect your repository
4. Set environment variables:
   - `API_KEY`: Your secret API key
   - `DATABASE_URL`: Will be set automatically by Railway (ensure it uses `postgresql+asyncpg://`)

## Custom GPT Integration

The API generates an OpenAPI 3.0 specification compatible with ChatGPT Custom GPT Actions:

1. Deploy the API
2. In ChatGPT, create a Custom GPT
3. Add an Action using the OpenAPI schema from `/openapi.json`
4. Configure authentication with Bearer token using your `API_KEY`

## API Endpoints

### Food Tracking
- `POST /api/v1/food` - Log food entry
- `GET /api/v1/food?date={date}` - Get entries for date
- `GET /api/v1/food/summary?date={date}` - Get daily summary
- `GET /api/v1/food/history?start={date}&end={date}` - Get history

### Ingredients
- `POST /api/v1/ingredients` - Add ingredient
- `GET /api/v1/ingredients` - List all
- `GET /api/v1/ingredients/search?q={query}` - Search
- `POST /api/v1/ingredients/{id}/set-default` - Set as default

### Recipes
- `POST /api/v1/recipes` - Create recipe
- `GET /api/v1/recipes` - List all
- `POST /api/v1/recipes/{id}/log?date={date}` - Log recipe as food

### Supplements
- `GET /api/v1/supplements` - List active supplements
- `GET /api/v1/supplements/all` - List all supplements

### Biomarkers
- `POST /api/v1/biomarkers` - Record reading
- `GET /api/v1/biomarkers?name={name}` - Get history
- `GET /api/v1/biomarkers/latest` - Get latest readings
- `GET /api/v1/biomarkers/compare` - Compare over time

### Exercises
- `POST /api/v1/exercises` - Log exercise
- `GET /api/v1/exercises?date={date}` - Get exercises

### Targets
- `POST /api/v1/targets` - Set target
- `GET /api/v1/targets` - Get current targets

### Dashboard
- `GET /api/v1/dashboard?date={date}` - Daily overview
