# API Authentication Setup

Your API now supports API Key authentication for security!

## How It Works

- If no `API_KEY` environment variable is set → API is **open** (development mode)
- If `API_KEY` is set → All requests require `X-API-Key` header with matching value

## Generate a Secure API Key

```bash
# On macOS/Linux - generates a 32-character random hex string
openssl rand -hex 32
```

Example output: `a3f5c8e9d2b1f4a6c7e8d9b0a1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0`

## Setup for Railway Deployment

### 1. Set Environment Variable in Railway

1. Go to your Railway dashboard
2. Select your `health-protocol-api` project
3. Go to **Variables** tab
4. Click **"+ New Variable"**
5. Add:
   - **Name:** `API_KEY`
   - **Value:** (paste your generated key)
6. Click **"Add"**
7. Railway will automatically redeploy with authentication enabled

### 2. Configure ChatGPT Custom GPT

1. Go to your Custom GPT settings
2. Scroll to **Actions**
3. Click on your existing action
4. Under **Authentication**, change from "None" to **"API Key"**
5. Configure:
   - **Auth Type:** API Key
   - **API Key:** (paste your API key)
   - **Auth Header Name:** `X-API-Key`

6. Click **Save**

### 3. Test It

Try in ChatGPT:
```
Add 50g protein, 60g carbs, and 20g fat for today
```

It should work seamlessly with authentication!

## Local Development

### Option 1: No Authentication (Easiest)
Just run the API without setting `API_KEY`:
```bash
python3 -m uvicorn main:app --reload
```
API will accept all requests without authentication.

### Option 2: With Authentication
Create a `.env` file:
```bash
cp .env.example .env
# Edit .env and set your API_KEY
```

Install python-dotenv:
```bash
pip3 install python-dotenv
```

Update `main.py` to load .env (optional - for local testing only):
```python
from dotenv import load_dotenv
load_dotenv()  # Add this before API_KEY = os.getenv("API_KEY")
```

## Testing with curl

### Without Authentication (when API_KEY not set):
```bash
curl http://localhost:8000/macros/
```

### With Authentication:
```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/macros/
```

### Invalid/Missing Key (returns 403):
```bash
curl http://localhost:8000/macros/
# Response: {"detail":"Invalid or missing API key. Provide X-API-Key header."}
```

## Security Best Practices

1. **Keep your API key secret** - Don't commit it to git (.env is in .gitignore)
2. **Use different keys** for development and production
3. **Rotate keys periodically** - Generate a new key and update Railway + ChatGPT
4. **Never share** your API key in screenshots or documentation

## Troubleshooting

### ChatGPT actions failing after enabling auth?
- Make sure you configured the API Key in ChatGPT Custom GPT settings
- Verify the header name is exactly: `X-API-Key`
- Check Railway logs to see if requests are being rejected

### Local testing not working?
- If you set `API_KEY`, make sure you're passing the header in curl
- Or unset `API_KEY` to test without auth: `unset API_KEY`

### Want to disable auth?
1. Remove the `API_KEY` variable from Railway
2. Railway will redeploy without authentication
3. Update ChatGPT to use "None" authentication
