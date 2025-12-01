# Health Protocol API

A fast web API for tracking health metrics like daily macros (protein, carbs, fat). Built with FastAPI and optimized for ChatGPT Custom GPT actions.

## Features

- **Fast & Lightweight**: Built with FastAPI and SQLite
- **ChatGPT Compatible**: Auto-generates OpenAPI specs for Custom GPT integration
- **Easy Updates**: Multiple endpoints for different update patterns
- **Persistent Storage**: SQLite database for reliable data storage
- **Flexible CRUD**: Create, read, update, and delete macro entries

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the API**:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Operations

- `POST /macros/` - Create or update a macro entry
- `GET /macros/` - Get all macro entries (ordered by date, newest first)
- `GET /macros/{date}` - Get entry for specific date (format: YYYY-MM-DD)
- `PATCH /macros/{date}` - Partially update entry (only provided fields)
- `PUT /macros/{date}/add` - Add to existing values (incremental update)
- `DELETE /macros/{date}` - Delete entry for specific date
- `GET /macros/{date}/summary` - Get entry with calculated calories

### Interactive Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Usage Examples

### Create or Update Entry
```bash
curl -X POST "http://localhost:8000/macros/" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-11-30",
    "protein": 150.5,
    "carbs": 200.0,
    "fat": 65.0
  }'
```

### Add to Existing Entry
```bash
curl -X PUT "http://localhost:8000/macros/2025-11-30/add" \
  -H "Content-Type: application/json" \
  -d '{
    "protein": 25.0,
    "carbs": 30.0,
    "fat": 10.0
  }'
```

### Get Entry with Summary
```bash
curl "http://localhost:8000/macros/2025-11-30/summary"
```

Response:
```json
{
  "date": "2025-11-30",
  "protein": 175.5,
  "carbs": 230.0,
  "fat": 75.0,
  "total_calories": 2295.0,
  "protein_calories": 702.0,
  "carbs_calories": 920.0,
  "fat_calories": 675.0
}
```

## ChatGPT Custom GPT Integration

### Option 1: Local Development (ngrok)

1. Install ngrok: `brew install ngrok` (or download from ngrok.com)
2. Start your API: `uvicorn main:app --reload`
3. Expose with ngrok: `ngrok http 8000`
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Option 2: Deploy to Production

Deploy to any hosting platform:
- **Railway**: Connect GitHub repo, auto-deploys
- **Render**: Free tier available
- **Fly.io**: Quick deployments
- **Heroku**: Classic option

### Configure ChatGPT Custom GPT

1. Go to ChatGPT → Create a GPT
2. In "Configure" → "Actions" → "Create new action"
3. Import the OpenAPI schema:
   - Use: `https://your-domain.com/openapi.json`
   - Or paste the schema from `/docs`
4. Set authentication to "None" (or add API key auth if needed)

### Suggested GPT Instructions

```
You are a health tracking assistant. Use the Health Protocol API to help users track their daily macros.

Available actions:
- Add macros for a date
- Get macros for a specific date
- View summaries with calculated calories
- Update or modify existing entries

When users mention eating food, ask for the macros and add them to today's date.
Always provide summaries showing total calories and macro breakdown.
```

## Data Model

### MacroEntry
- `id`: Integer (auto-generated)
- `date`: Date (YYYY-MM-DD, unique)
- `protein`: Float (grams, default: 0.0)
- `carbs`: Float (grams, default: 0.0)
- `fat`: Float (grams, default: 0.0)

## Development

### Project Structure
```
health_protocol/
├── main.py           # FastAPI application
├── models.py         # SQLAlchemy models
├── schemas.py        # Pydantic schemas
├── database.py       # Database configuration
├── requirements.txt  # Python dependencies
└── README.md
```

### Database
The API uses SQLite with a file named `health_protocol.db` created automatically on first run.

## Extending the API

To add new tables/tracking capabilities:

1. Add model in `models.py`
2. Create schemas in `schemas.py`
3. Add endpoints in `main.py`
4. Database tables are created automatically

Example structure is already in place for macros - follow the same pattern for additional metrics.
