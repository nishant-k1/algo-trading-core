# algo-trading-core

Backend API for the algo trading app (FastAPI). Deploy on **Render**.

## Push to GitHub

1. Create a new repo on GitHub named `algo-trading-core` (no README/license).
2. Then run:

```bash
cd /Users/nishantkumar/dev/algo-trading-core
git remote add origin https://github.com/YOUR_USERNAME/algo-trading-core.git
git push -u origin main
```

## Deploy on Render

### Option A: Docker (recommended)

- **Environment:** Docker
- **Dockerfile path:** `./Dockerfile` (root of repo)
- **No build/start commands needed** — Render uses the Dockerfile. The app listens on `PORT` (set by Render).
- **Environment variables:** Set in Render dashboard: `DATABASE_URL`, `REDIS_URL` (if used), `SECRET_KEY`, `FRONTEND_URL` (your Vercel app URL for CORS).

### Option B: Native (Python)

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** Same as above.
