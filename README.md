# FairCart

FairCart is a demo marketplace for **fair product exposure in online marketplaces**. Instead of ranking only by popularity, the storefront combines product quality, engagement, freshness, low-exposure boosts, and seller diversity so new or small sellers can still be discovered.

FairCart is split into two main app folders:

- `backend/` Flask API, MongoDB integration, ML data, and backend tools
- `frontend/` storefront and admin frontend

## Core Features

- Fair discovery ranking with decaying low-impression boosts
- Seller-diversity re-ranking so one seller cannot dominate a page
- Customer storefront with fair score badges and product recommendations
- Seller dashboard with product quality, impressions, clicks, CTR, and exposure status
- Admin fairness monitor with visibility share, fairness index, and monopoly alerts
- AI-assisted seller listing tools with image upload and moderation hooks

## Local Setup

1. Create or reuse the repo virtual environment in `.venv/`.
2. Install backend dependencies:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Configure backend environment:

```powershell
Copy-Item .env.example .env
```

Update `backend/.env` with:

- `MONGO_URI`
- `SECRET_KEY`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `OPENAI_API_KEY`
- `FLASK_ENV`
- `CORS_ORIGINS`

## Run Locally

Backend:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe app.py
```

Frontend:

```powershell
Set-Location frontend
..\.venv\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1
```

URLs:

- Storefront: `http://127.0.0.1:8000/s-frontend/index.html`
- Admin: `http://127.0.0.1:8000/admin-frontend/admin.html`
- Integrated backend-served app: `http://localhost:5000`

## Useful Backend Tools

- Seed realistic matched catalog data: `backend/tools/maintenance/seed_real_market.py`
- Seed sample market data: `backend/tools/maintenance/populate_market.py`
- Inspect ML files: `backend/tools/diagnostics/check_behavior.py`
- See tool layout: `backend/tools/README.md`

## Production Notes

- Serve the Flask app from `backend/app.py`
- Keep secrets in environment variables, not committed files
- Put a reverse proxy like Nginx in front of the backend
- Use the `/health` endpoint for health checks
