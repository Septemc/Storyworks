# Storyworks Apps

This directory contains the phase-one application skeleton.

## Layout

- `frontend/`: Vue 3 + Vite client
- `backend/`: FastAPI service

## Backend

```bash
cd apps/backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

By default, the frontend expects the backend at `http://127.0.0.1:8000`.
