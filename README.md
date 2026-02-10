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

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** Set `DATABASE_URL`, `REDIS_URL` (if used), `SECRET_KEY`, and `FRONTEND_URL` (your Vercel app URL for CORS).
