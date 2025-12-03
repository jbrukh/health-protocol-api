---
name: withings
description: Access Withings health device data including weight, body composition, blood pressure, heart rate, activity (steps/calories), and sleep. Use when user asks about their weight, body measurements, steps, activity, sleep data, or health metrics from Withings devices.
---

# Withings Health Data Skill

Access health data from Withings devices (smart scales, blood pressure monitors, sleep trackers, fitness watches).

## Credentials

All Withings credentials are in `skill/withings-tokens.json` (relative to project root):
```json
{
  "withings_client_id": "your-client-id",
  "withings_client_secret": "your-client-secret",
  "access_token": "current-access-token",
  "refresh_token": "refresh-token-for-renewal"
}
```

## Making API Requests

1. Read the `access_token` from `skill/withings-tokens.json`
2. Include header: `Authorization: Bearer <access_token>`
3. All Withings API endpoints use POST requests with form data

## Refreshing Expired Tokens

Access tokens expire after 3 hours. If you get a 401 or expired token error:

```bash
# Read all credentials from skill/withings-tokens.json
CLIENT_ID=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['withings_client_id'])")
CLIENT_SECRET=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['withings_client_secret'])")
REFRESH_TOKEN=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")

curl -X POST "https://wbsapi.withings.net/v2/oauth2" \
  -d "action=requesttoken" \
  -d "grant_type=refresh_token" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "refresh_token=$REFRESH_TOKEN"
```

Update `skill/withings-tokens.json` with the new `access_token` and `refresh_token` from the response.

## API Endpoints

### Get Body Measurements

Fetches weight, body composition, blood pressure, heart rate.

```bash
ACCESS_TOKEN=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
END_DATE=$(date +%s)
START_DATE=$((END_DATE - 604800))  # 7 days ago

curl -X POST "https://wbsapi.withings.net/measure" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "action=getmeas" \
  -d "startdate=$START_DATE" \
  -d "enddate=$END_DATE" \
  -d "category=1"
```

**Measurement Types:**
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

**Decoding Values:**
Values are encoded as `value * 10^unit`. Example: `{"value": 10569, "unit": -2}` = 105.69 kg

### Get Activity Data

Fetches steps, calories, distance.

```bash
ACCESS_TOKEN=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
START_DATE=$(date -v-7d +%Y-%m-%d)  # 7 days ago (macOS)
END_DATE=$(date +%Y-%m-%d)

curl -X POST "https://wbsapi.withings.net/v2/measure" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "action=getactivity" \
  -d "startdateymd=$START_DATE" \
  -d "enddateymd=$END_DATE"
```

**Response Fields:**
- `steps`: Daily step count
- `distance`: Distance in meters
- `calories`: Calories burned
- `totalcalories`: Active calories
- `soft`: Light activity (seconds)
- `moderate`: Moderate activity (seconds)
- `intense`: Intense activity (seconds)

### Get Sleep Data

```bash
ACCESS_TOKEN=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
START_DATE=$(date -v-7d +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

curl -X POST "https://wbsapi.withings.net/v2/sleep" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "action=getsummary" \
  -d "startdateymd=$START_DATE" \
  -d "enddateymd=$END_DATE"
```

**Response Fields:**
- `lightsleepduration`: Light sleep (seconds)
- `deepsleepduration`: Deep sleep (seconds)
- `remsleepduration`: REM sleep (seconds)
- `wakeupduration`: Time awake (seconds)
- `sleep_score`: Sleep quality score

## Quick Reference

| User Says | Action |
|-----------|--------|
| "What's my weight?" | GET measurements, filter type=1 |
| "Show body composition" | GET measurements, types 1,5,6,8,76,88 |
| "How many steps today?" | GET activity for today |
| "Activity this week" | GET activity last 7 days |
| "Blood pressure readings" | GET measurements, types 9,10 |
| "Heart rate history" | GET measurements, type=11 |
| "How did I sleep?" | GET sleep data |
| "Weight trend this month" | GET measurements last 30 days, type=1 |

## Example: Get Latest Weight

```bash
# One-liner to get latest weight
ACCESS_TOKEN=$(cat skill/withings-tokens.json | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -X POST "https://wbsapi.withings.net/measure" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "action=getmeas" \
  -d "startdate=$(($(date +%s) - 86400))" \
  -d "enddate=$(date +%s)" \
  -d "category=1" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for grp in data.get('body', {}).get('measuregrps', []):
    for m in grp['measures']:
        if m['type'] == 1:  # Weight
            val = m['value'] * (10 ** m['unit'])
            print(f'Weight: {val:.1f} kg ({val * 2.20462:.1f} lbs)')
"
```

## Unit Conversions

- **kg to lbs**: multiply by 2.20462
- **cm to inches**: multiply by 0.393701
- **meters to feet**: multiply by 3.28084

## Notes

- Timestamps for measurements API use Unix epoch (seconds)
- Activity/sleep APIs use YYYY-MM-DD date format
- `category=1` returns only real measurements (not goals)
- Access tokens expire in 3 hours; refresh as needed
