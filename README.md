# Eye ROI Analyzer for Diabetic Retinopathy

Beginner-friendly full-stack web app:

- **Frontend**: React + Tailwind (Vite)
- **Backend**: FastAPI
- **ML**: TensorFlow/Keras (EfficientNet preprocessing; supports your trained model)
- **Storage**: Azure Blob Storage (or local fallback)
- **Database**: Azure Cosmos DB (Mongo API) (or local JSON fallback)
- **Reports**: PDF generation (ReportLab)

> Important: The project runs end-to-end **without Azure** (local fallback).  
> To get **real medical predictions**, you must provide a trained DR model at `backend/app/models/dr_model.keras` (or set `MODEL_PATH`).

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Test: `http://localhost:8000/health`

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open: `http://localhost:5173`

## API

- `POST /predict` (multipart/form-data)
  - `image` (file)
  - `name`, `age`, `gender`, `diabetes_duration`, `sugar_level` (form fields)
- `GET /reports/<filename>` serves generated PDF reports

## Azure deployment guide (Student-friendly)

### 1) Create Azure resources

#### A) Storage Account + Blob Container

- In Azure Portal: **Storage accounts** → Create
  - **Redundancy**: LRS (cheap)
  - After create → **Data storage > Containers** → Create container
    - Name: `retina-images`
    - Public access: **Private** (recommended)

Get connection string:
- Storage account → **Access keys** → Connection string

#### B) Cosmos DB (Mongo API)

- Azure Portal: **Azure Cosmos DB** → Create
  - API: **MongoDB**
  - Choose free/student-friendly tier if available

Get Mongo connection string:
- Cosmos DB account → **Connection strings**

### 2) Deploy FastAPI backend to Azure App Service

#### Option A (beginner-friendly): Deploy from VS Code / Zip Deploy

1. Create an App Service:
   - **App Services** → Create
   - Publish: **Code**
   - Runtime: **Python 3.11** (or closest available)

2. Set App Service configuration:
   - App Service → **Configuration** → **Application settings** → Add:
     - `AZURE_STORAGE_CONNECTION_STRING`
     - `AZURE_BLOB_CONTAINER_NAME` = `retina-images`
     - `COSMOS_MONGO_URI`
     - `COSMOS_DB_NAME` = `eye_roi_analyzer`
     - `COSMOS_COLLECTION_NAME` = `predictions`
     - `FRONTEND_ORIGIN` = your frontend URL (later)
     - `ENVIRONMENT` = `azure`

3. Startup command (App Service → Configuration → General settings):

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Deploy backend code
   - Deploy the `backend/` folder contents.
   - Ensure `requirements.txt` is at the root of the deployed backend.

#### Notes about TensorFlow on Azure App Service

- TensorFlow can be heavy. If App Service build fails or is slow:
  - Use a smaller model, or
  - Switch to a Linux plan with more memory, or
  - Replace `tensorflow` with `tensorflow-cpu` (often easier on servers).

### 3) Deploy frontend (Static Web App or any static host)

#### Option A: Azure Static Web Apps

1. Build locally:

```bash
cd frontend
npm run build
```

2. Set `VITE_API_BASE` to your backend URL in `.env` and rebuild:

```bash
setx VITE_API_BASE "https://<your-backend>.azurewebsites.net"
```

3. Upload `frontend/dist/` to your static hosting.

### 4) Update CORS

Set backend `FRONTEND_ORIGIN` to your deployed frontend URL in App Service Configuration.

## Where data is stored

- **Images**
  - Azure configured: Blob container `retina-images`
  - Otherwise: `backend/storage/images/`
- **Predictions metadata**
  - Azure configured: Cosmos DB (Mongo API)
  - Otherwise: `backend/storage/db.json`
- **PDF reports**
  - Always generated to `backend/storage/reports/` and served at `/reports/...`

