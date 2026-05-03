# Backend (FastAPI)

## Quick start (local)

1. Create venv and install deps:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create `.env`:

```bash
copy .env.example .env
```

3. Run API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be at `http://localhost:8000`.

## Notes

- If Azure credentials are **not** set, images + DB writes fall back to local `backend/storage/`.
- Put your trained Keras model at the path in `MODEL_PATH` (default: `app/models/dr_model.keras`).

