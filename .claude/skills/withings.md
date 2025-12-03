---
name: withings
description: Access Withings health device data including weight, body composition, blood pressure, heart rate, activity (steps/calories), and sleep. Use when user asks about their weight, body measurements, steps, activity, sleep data, or health metrics from Withings devices.
---

# Withings Health Data Skill

Access health data from Withings devices (smart scales, blood pressure monitors, sleep trackers, fitness watches).

## Authentication

**API credentials** are stored in `~/.health-api-credentials.json`:
```json
{
  "withings_client_id": "your-client-id",
  "withings_client_secret": "your-client-secret"
}
```

**OAuth tokens** are stored in `~/.withings_tokens.json`:
- `access_token`: Bearer token for API requests (expires in 3 hours)
- `refresh_token`: Used to get new access tokens when expired

### Refreshing Expired Tokens

If you get a 401 error or token expired message, refresh the token using the helper script:

```bash
python /Users/jbrukh/Documents/protocol/withings.py refresh
```

Or manually with credentials from `~/.health-api-credentials.json`:

```bash
curl -X POST "https://wbsapi.withings.net/v2/oauth2" \
  -d "action=requesttoken" \
  -d "grant_type=refresh_token" \
  -d "client_id=<withings_client_id>" \
  -d "client_secret=<withings_client_secret>" \
  -d "refresh_token=<REFRESH_TOKEN_FROM_~/.withings_tokens.json>"
```

Save the new tokens to `~/.withings_tokens.json`.

## API Endpoints

All requests require: `Authorization: Bearer <access_token>`

### Get Body Measurements (Weight, Body Composition, Blood Pressure, Heart Rate)

```bash
curl -X POST "https://wbsapi.withings.net/measure" \
  -H "Authorization: Bearer <access_token>" \
  -d "action=getmeas" \
  -d "startdate=<unix_timestamp>" \
  -d "enddate=<unix_timestamp>" \
  -d "category=1"
```

**Response contains measure groups with types:**
| Type | Measurement | Unit |
|------|-------------|------|
| 1 | Weight | kg |
| 4 | Height | m |
| 5 | Fat Free Mass | kg |
| 6 | Fat Ratio | % |
| 8 | Fat Mass Weight | kg |
| 9 | Diastolic Blood Pressure | mmHg |
| 10 | Systolic Blood Pressure | mmHg |
| 11 | Heart Pulse | bpm |
| 76 | Muscle Mass | kg |
| 77 | Hydration | kg |
| 88 | Bone Mass | kg |

**Decoding values:** `actual_value = value * 10^unit`
Example: `{"value": 10569, "unit": -2}` = 105.69 kg

### Get Activity Data (Steps, Calories, Distance)

```bash
curl -X POST "https://wbsapi.withings.net/v2/measure" \
  -H "Authorization: Bearer <access_token>" \
  -d "action=getactivity" \
  -d "startdateymd=2025-01-01" \
  -d "enddateymd=2025-01-15"
```

**Response fields:**
- `steps`: Daily step count
- `distance`: Distance in meters
- `calories`: Calories burned
- `totalcalories`: Active calories
- `soft`: Light activity duration (seconds)
- `moderate`: Moderate activity duration (seconds)
- `intense`: Intense activity duration (seconds)

### Get Sleep Data

```bash
curl -X POST "https://wbsapi.withings.net/v2/sleep" \
  -H "Authorization: Bearer <access_token>" \
  -d "action=getsummary" \
  -d "startdateymd=2025-01-01" \
  -d "enddateymd=2025-01-15"
```

**Response fields:**
- `lightsleepduration`: Light sleep seconds
- `deepsleepduration`: Deep sleep seconds
- `remsleepduration`: REM sleep seconds
- `wakeupduration`: Time awake seconds
- `sleep_score`: Sleep quality score

## Quick Reference

| User Says | Action |
|-----------|--------|
| "What's my weight?" | GET measurements, filter type=1 |
| "Show my body composition" | GET measurements, show types 1,5,6,8,76,88 |
| "How many steps today?" | GET activity for today |
| "My activity this week" | GET activity last 7 days |
| "Blood pressure readings" | GET measurements, filter types 9,10 |
| "Heart rate history" | GET measurements, filter type=11 |
| "How did I sleep?" | GET sleep data |
| "Weight trend this month" | GET measurements last 30 days, filter type=1 |

## Helper Script

For convenience, use the withings.py script at `/Users/jbrukh/Documents/protocol/withings.py`:

```bash
# Fetch last 30 days of data
python /Users/jbrukh/Documents/protocol/withings.py fetch

# Fetch last N days
python /Users/jbrukh/Documents/protocol/withings.py fetch 7

# Refresh tokens manually
python /Users/jbrukh/Documents/protocol/withings.py refresh
```

This outputs data to `withings_data_YYYYMMDD.json` with parsed, readable values.

## Example: Get Latest Weight

```bash
# Read token
ACCESS_TOKEN=$(cat ~/.withings_tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Get measurements from last 7 days
END_DATE=$(date +%s)
START_DATE=$((END_DATE - 604800))

curl -s -X POST "https://wbsapi.withings.net/measure" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "action=getmeas" \
  -d "startdate=$START_DATE" \
  -d "enddate=$END_DATE" \
  -d "category=1"
```

## Important Notes

- Access tokens expire after 3 hours; use refresh token to get new ones
- Timestamps use Unix epoch format for measurements API
- Activity/sleep APIs use YYYY-MM-DD date format
- Category=1 returns only real measurements (not goals/objectives)
- Weight is returned in kg; convert to lbs by multiplying by 2.20462
