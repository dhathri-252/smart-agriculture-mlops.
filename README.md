# Smart Agriculture Prediction System with MLOps

AI-powered crop recommendation: soil + climate inputs → Random Forest predicts the best of 22 crops. FastAPI backend, React frontend, MLflow tracking, DVC versioning, Docker-ready.

## Overview
Farmers enter N, P, K, temperature, humidity, pH, rainfall and get an instant crop recommendation from a trained Random Forest classifier.

## Problem Statement
Choosing the wrong crop for soil/climate conditions reduces yield. This system learns crop-condition patterns from 2,200 labeled samples and recommends the most suitable crop.

## Objectives
- Preprocess + stratified split of crop dataset
- Train/compare Logistic Regression, Decision Tree, Random Forest
- Serve best model via FastAPI (`POST /predict`)
- React UI usable on laptop + Android mobile
- Track with MLflow + DVC; Docker reproducible

## Features
- 7-field prediction form with validation + example fill
- Result card + Predict Again flow
- Friendly errors for missing/invalid/offline states
- Custom `/api-docs` (Swagger) + `/redoc` pages
- Responsive layout (900px/600px breakpoints), 44px touch targets

## Technology Stack
Backend: Python 3.11, FastAPI 0.141.1, Uvicorn 0.54.0, scikit-learn 1.9.1, pandas 3.0.6, joblib. Frontend: React 18, Vite 6, Node 20. MLOps: MLflow 3.16.1, DVC 3.67.1. Infra: Docker (python:3.11-slim + node:20-alpine/nginx).

## Architecture
Browser (laptop/Android) → React (Vite :5173 / nginx :80) → FastAPI (:8000) → src/predict.py → models/crop_recommendation_model.pkl (RandomForest) → {recommended_crop}.

## Folder Structure
api/ (main.py, docs.py); src/ (data_preprocessing, train, evaluate, predict); data/raw/crop_recommendation.csv (+ .dvc); data/processed/ (X/y train/test); models/crop_recommendation_model.pkl; mlruns/ (MLflow store); frontend/src/ (App, Header, Hero, Stats, PredictionForm, PredictionResult, About); notebooks/exploration.ipynb; Dockerfile.backend, Dockerfile.frontend, docker-compose.yml; requirements.txt.

## Dataset
data/raw/crop_recommendation.csv — 2,200 rows x 8 cols (N,P,K,temperature,humidity,ph,rainfall,label), 22 crops x 100 samples, 0 nulls. DVC-tracked (md5 fa83739710074b21a20b156034538279).

## Data Preprocessing
Validate schema/nulls/duplicates → stratified 80/20 split (random_state=42) → X_train 1760x7, X_test 440x7, y_train 1760, y_test 440.

## EDA
See notebooks/exploration.ipynb (distributions, correlations, per-crop profiles).

## ML Models (src/train.py)

## Evaluation Results (actual MLflow run a04bfe39)
Random Forest on 440-sample test set: accuracy 0.9955, macro-precision 0.9957, macro-recall 0.9955, macro-F1 0.9955.

## Selected Model
models/crop_recommendation_model.pkl (3.4 MB) — RandomForestClassifier(n_estimators=100, random_state=42).

## Prediction Pipeline (src/predict.py)
predict_crop(N,P,K,temperature,humidity,ph,rainfall) validates numeric/non-None/non-NaN (bool rejected), builds DataFrame in exact feature order, uses cached joblib model. Verified: rice sample → "rice"; string/None raise ValueError.

## MLflow
Experiment Smart-Agriculture-Crop-Recommendation, run RandomForest-Training-Run. Params: model_type=RandomForestClassifier, n_estimators=100, random_state=42, train_samples=1760, test_samples=440. Metrics above. Artifact: MLmodel, model.skops, input_example.json under mlruns/674862982060791979/models/m-041c0c96.../artifacts/.

## DVC
data/raw/crop_recommendation.csv.dvc tracks raw data; dvc status = up to date. No remote configured (local default).

## FastAPI (api/main.py v1.0.0)
GET / → {"message":"Smart Agriculture Prediction API is running"}. GET /health → {"status":"healthy"}. POST /predict (N,P,K,temperature,humidity,ph,rainfall floats) → {"recommended_crop":"rice"}; 422 on missing/invalid. CORS: localhost:5173 + 127.0.0.1:5173 + CORS_ALLOW_ORIGINS extras.

## React Frontend
Header/Hero/Stats/PredictionForm/PredictionResult/About. API base = import.meta.env.VITE_API_URL fallback http://127.0.0.1:8000. Dev: npm run dev (:5173).

## Responsive / Mobile
Breakpoints 900px + 600px; inputs font-size 16px, min-height 44px, width 100%. Rice prediction + validation pass on desktop + Android UAs.

## Docker
Dockerfile.backend (python:3.11-slim, :8000). Dockerfile.frontend (node:20-alpine build ARG VITE_API_URL, nginx :80). docker-compose.yml (backend :8000, frontend :8080→80). NOTE: Docker Engine not installed here, so build/run not executed — compose YAML validated.

## Installation
python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt; cd frontend && npm install.

## Run Locally
.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000. cd frontend && npm run dev.

## Run with Docker
docker compose up --build (frontend http://localhost:8080, backend http://localhost:8000).

## API Docs
/api-docs (Swagger), /redoc (ReDoc), /openapi.json.

## Example Request
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"N":90,"P":42,"K":43,"temperature":20.87,"humidity":82,"ph":6.50,"rainfall":202.93}'

## Example Response
{"recommended_crop": "rice"}

## Testing
Manual: GET /, GET /health, rice POST → rice; {} → 422; N:"abc" → 422; frontend validation + offline banner. tests/ empty (no automated suite yet).

## Future Improvements
pytest + CI; DVC remote + dvc.yaml; MLflow server; per-env VITE_API_URL + free hosting (Render/Fly + Vercel/Netlify); crop info cards; hamburger nav.

Logistic Regression (max_iter=1000), Decision Tree, Random Forest (n_estimators=100), all random_state=42. Selection = highest test macro-F1 then accuracy.
