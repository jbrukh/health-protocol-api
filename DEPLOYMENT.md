# Deployment Guide

Your API is ready to deploy! Here are the easiest options, ranked by simplicity:

## Option 1: Railway (Easiest - Recommended)

**Why Railway:** Free tier, auto-deploys from GitHub, zero configuration needed.

### Steps:
1. **Initialize git and push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Health Protocol API"
   gh repo create health-protocol-api --public --source=. --push
   ```

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `health-protocol-api` repository
   - Railway auto-detects Python and deploys

3. **Get your URL:**
   - Railway provides a URL like: `https://health-protocol-api.railway.app`
   - Use this URL in ChatGPT Custom GPT

**Time to deploy:** ~2 minutes

---

## Option 2: Render (Free Tier Available)

**Why Render:** Generous free tier, simple setup, good for side projects.

### Steps:
1. **Push to GitHub** (same as Railway step 1)

2. **Deploy to Render:**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render auto-detects the `render.yaml` configuration

3. **Settings:**
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Free tier limitations:** Spins down after 15 mins of inactivity (first request may be slow)

---

## Option 3: Fly.io (Good Free Tier)

**Why Fly.io:** Fast global deployment, good free tier, modern platform.

### Steps:
1. **Install Fly CLI:**
   ```bash
   brew install flyctl
   ```

2. **Login and deploy:**
   ```bash
   flyctl auth login
   flyctl launch
   # Answer prompts (use defaults)
   flyctl deploy
   ```

3. **Get your URL:**
   ```bash
   flyctl apps open
   ```

**Free tier:** 3 VMs with 256MB RAM each

---

## Option 4: Quick Test with ngrok (For Testing Only)

**Why ngrok:** Test ChatGPT integration immediately, no deployment needed.

### Steps:
1. **Install ngrok:**
   ```bash
   brew install ngrok
   ```

2. **Start your API:**
   ```bash
   python3 -m uvicorn main:app --reload
   ```

3. **Expose with ngrok (in another terminal):**
   ```bash
   ngrok http 8000
   ```

4. **Use the HTTPS URL:**
   - ngrok provides: `https://abc123.ngrok.io`
   - Use this in ChatGPT Custom GPT
   - **Note:** URL changes every time you restart ngrok

**Best for:** Quick testing before permanent deployment

---

## Option 5: Docker Deployment (Any Platform)

**Why Docker:** Works on any cloud provider (AWS, GCP, Azure, DigitalOcean).

### Steps:
1. **Build the image:**
   ```bash
   docker build -t health-protocol-api .
   ```

2. **Run locally to test:**
   ```bash
   docker run -p 8000:8000 health-protocol-api
   ```

3. **Deploy to any platform:**
   - Push to Docker Hub or container registry
   - Deploy to AWS ECS, Google Cloud Run, Azure Container Instances, etc.

---

## After Deployment: ChatGPT Integration

1. **Get your deployed URL** (e.g., `https://your-app.railway.app`)

2. **Create ChatGPT Custom GPT:**
   - Go to ChatGPT → Explore GPTs → Create
   - Name it "Health Tracker" or similar
   - In Configure tab → Actions → Create new action

3. **Import OpenAPI Schema:**
   - Method 1: Paste URL: `https://your-app.railway.app/openapi.json`
   - Method 2: Copy/paste schema from `https://your-app.railway.app/docs`

4. **Test it:**
   - Ask ChatGPT: "Add 50g protein, 60g carbs, and 20g fat for today"
   - Ask: "What are my macros for today?"
   - Ask: "Show me my total calories"

---

## Database Persistence

**Important:** SQLite database file is stored locally on the deployment server.

- **Railway/Render/Fly.io:** Database persists across deployments
- **For production:** Consider upgrading to PostgreSQL:
  - Railway/Render offer free PostgreSQL databases
  - Only requires changing the `SQLALCHEMY_DATABASE_URL` in `database.py`

---

## Monitoring Your Deployment

### Railway:
```bash
# View logs
Visit dashboard → Select project → Deployments → View logs
```

### Render:
```bash
# View logs
Visit dashboard → Select service → Logs tab
```

### Fly.io:
```bash
flyctl logs
```

---

## Recommended: Start with Railway

For ChatGPT integration, I recommend **Railway** because:
- ✅ Fastest setup (2 minutes)
- ✅ Free tier sufficient for personal use
- ✅ Auto-deploys on git push
- ✅ Persistent database
- ✅ Always-on (no cold starts)
- ✅ Easy to upgrade if needed

**Next steps:**
1. Create GitHub repo
2. Deploy to Railway
3. Copy the URL
4. Add to ChatGPT Custom GPT
5. Start tracking your macros!
