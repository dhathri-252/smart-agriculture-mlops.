# 🌱 Smart Agriculture Prediction System with MLOps

AI-powered crop recommendation platform for farmers: enter soil and climate values and a trained Random Forest model recommends the most suitable crop — with real confidence scores, farmer-friendly crop guidance, prediction history, a dashboard, an agriculture assistant, weather support, smart farming recommendations, and full **English + Telugu** UI.

---

## Problem Statement

Choosing the wrong crop for local soil and climate conditions reduces yield and income. Small farmers often lack access to data-driven guidance at decision time. This system learns crop–condition patterns from 2,200 labelled samples covering 22 crops and recommends the most suitable crop instantly, then wraps that prediction in practical, understandable farming information.

## Objectives

- Preprocess the crop dataset with validation and a stratified 80/20 split
- Train and compare Logistic Regression, Decision Tree and Random Forest; select the best by measured test metrics
- Serve the best model through a production-oriented FastAPI backend
- Provide a responsive React UI usable on laptop and Android phones
- Track experiments with MLflow and dataset versions with DVC
- Add history, dashboard, assistant, weather and recommendation features without breaking the original prediction flow
- Keep everything reproducible with Docker

## Features

**Core prediction**
- 7-field prediction form (N, P, K, temperature, humidity, pH, rainfall) with validation, loading, error and example-fill states
- **Top-3 crop recommendations** from the model's real `predict_proba` values — no fabricated confidence
- **Confidence meter** showing the model's own probability for the recommended crop
- Farmer-friendly **crop information card**: dataset-derived temperature/humidity/rainfall/pH ranges, typical N-P-K, soil, irrigation, fertiliser and cultivation guidance (bilingual)
- **Input-range warnings** when values fall outside the training data (lightweight data-drift check)

**Platform**
- **Prediction history** stored safely in SQLite (inputs, crop, confidence, timestamp) with list/clear APIs
- **Farmer dashboard**: totals, recent prediction, most frequent crop, CSS bar chart, history table, farming tips
- **Agriculture assistant** chat with a provider abstraction (built-in bilingual knowledge base; optional OpenAI-compatible provider) and clear disclaimers
- **Weather** integration (OpenWeatherMap server-side key) with a clean "not configured" fallback — never fabricates data
- **Smart farming recommendations** combining prediction + soil inputs + optional weather, phrased as guidance ("recommended", "consider", "may be suitable")
- **Authentication**: register/login/logout, PBKDF2-hashed passwords, HMAC-signed tokens, basic farmer profile — prediction stays public
- **Admin/monitoring** endpoint (`X-Admin-Token`) with prediction counts, recent activity, model info, health and system stats
- **Bilingual (English / తెలుగు)**: centralized translation dictionary (134 keys per language), header switcher, persisted choice

## Architecture

```
Browser (laptop / Android)
   │
   ▼
React + Vite frontend ── nginx (Docker) :8080  /  vite dev :5173
   │   fetch /predict, /api/*
   ▼
FastAPI backend :8000  (api/main.py → api/routers/*)
   ├── src/predict.py        → models/crop_recommendation_model.pkl (RandomForest)
   ├── src/crop_info.py      → bilingual crop guidance (dataset-derived ranges)
   ├── api/db.py             → SQLite (history + users) at data/app.db
   ├── api/services/         → assistant (KB / OpenAI) + weather (OWM / none)
   └── MLflow mlruns/ · DVC-tracked data/
```

## Technologies

| Layer | Stack |
|---|---|
| Backend | Python 3.11, FastAPI 0.141.1, Uvicorn 0.54.0, Pydantic 2.13.5 |
| ML | scikit-learn 1.9.1, pandas 3.0.6, numpy 2.4.6, joblib 1.6.0 |
| Frontend | React 18, Vite 6, plain CSS (no UI framework) |
| MLOps | MLflow 3.16.1 (local file store), DVC 3.67.1 |
| Persistence | SQLite via Python stdlib (no external database) |
| Security | PBKDF2-HMAC-SHA256 password hashing, HMAC-signed tokens (stdlib) |
| Infra | Docker (`python:3.11-slim` backend, `node:20-alpine` + `nginx:alpine` frontend) |
| Testing | pytest, httpx (TestClient), `vite build` |

## ML Model

- **Algorithm:** `RandomForestClassifier(n_estimators=100, random_state=42)`
- **Selection:** three candidates trained (Logistic Regression, Decision Tree, Random Forest); best chosen by test macro-F1 then accuracy
- **Test results:** accuracy **0.9955**, macro-precision 0.9957, macro-recall 0.9955, macro-F1 **0.9955** (440-sample test set)
- **Inputs:** N, P, K, temperature, humidity, ph, rainfall (7 features) → 22 crop classes
- **Probabilities:** `predict_proba` is supported, so confidence and top-3 values are real model outputs
- **Artifact:** `models/crop_recommendation_model.pkl` (loaded lazily and cached)
- **Supporting file:** `models/training_stats.json` — per-feature min/max/mean of the training data used for input-range warnings (derived from existing data; the model was **not** retrained)

## Dataset

`data/raw/crop_recommendation.csv` — **2,200 rows × 8 columns** (`N, P, K, temperature, humidity, ph, rainfall, label`), 22 crops × 100 samples each, 0 nulls.

- DVC-tracked (md5 `fa83739710074b21a20b156034538279`); `dvc status` = up to date (no remote configured — local cache only)
- Stratified 80/20 split (`random_state=42`) → X_train 1760×7, X_test 440×7 → `data/processed/`
- EDA notebook: `notebooks/exploration.ipynb`

## MLOps Workflow

1. **Version data** — DVC tracks the raw CSV
2. **Preprocess** — `src/data_preprocessing.py` validates schema/nulls/duplicates and creates the stratified split
3. **Train & select** — `src/train.py` trains 3 candidates, prints a metrics comparison table, selects the best
4. **Track experiments** — MLflow logs params (`model_type`, `n_estimators`, `random_state`, sample counts), metrics (accuracy/precision/recall/F1) and the model artifact to `mlruns/` (experiment `Smart-Agriculture-Crop-Recommendation`)
5. **Evaluate** — `src/evaluate.py` computes metrics + classification report
6. **Serve** — FastAPI loads the pickle and serves `POST /predict`
7. **Monitor** — request logging middleware, `/health` with model status, token-protected `/api/admin/stats`, input-range drift warnings on every prediction

## API Information

Base URL (local): `http://localhost:8000` — interactive docs at **`/api-docs`** (Swagger UI) and `/redoc`; OpenAPI JSON at `/openapi.json`.

| Method | Path | Description |
|---|---|---|
| GET | `/` | API info |
| GET | `/health` | Health + model status + uptime |
| POST | `/predict` | Crop prediction: top-3, confidence, crop info, drift warnings, history record |
| GET | `/api/history?limit=&mine=` | Prediction history (list, most recent first) |
| DELETE | `/api/history?mine=` | Clear history (`mine=true` only clears the logged-in user's) |
| POST | `/api/recommendations` | Smart farming recommendations (soil + prediction + optional weather) |
| POST | `/api/assistant` | Ask the agriculture assistant `{question, language: en\|te}` |
| GET | `/api/weather?location=` | Current weather + suggestions, or a clean "not configured" state |
| POST | `/api/auth/register` | Create account → signed token (201; 409 if taken) |
| POST | `/api/auth/login` | Log in → signed token (401 on bad credentials) |
| GET | `/api/auth/me` | Current user (Bearer token) |
| PUT | `/api/auth/profile` | Update farm name / location |
| POST | `/api/auth/logout` | Confirms logout (client discards token) |
| GET | `/api/admin/stats` | Admin stats — requires `X-Admin-Token` (503 if unconfigured, 401 if wrong) |

Example:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"N":90,"P":42,"K":43,"temperature":20.87,"humidity":82,"ph":6.5,"rainfall":202.93}'
```

Response (abbreviated): `{"recommended_crop":"rice","confidence":0.9,"top_predictions":[{"crop":"rice","probability":0.9},...],"crop_info":{...},"input_warnings":[]}`

Validation errors return **422** with field details; a missing model returns **503**.

## Frontend Information

- React 18 + Vite 6, plain CSS with the existing green agriculture theme (900px / 600px breakpoints)
- Views: **Home** (hero, stats, prediction form, about), **Dashboard** (stats, chart, history, tips), **Assistant** (chat), **Weather** — simple state-based navigation, no router dependency
- API base URL from `VITE_API_URL` (falls back to `http://127.0.0.1:8000`)
- Centralized i18n: `src/i18n/translations.js` + `LanguageContext` (EN/తెలుగు, persisted in localStorage, switcher in the header)
- Auth token stored in localStorage and attached automatically via `src/api.js`
- Loading, error and empty states throughout; accessible labels/roles on forms and navigation

## Docker Setup

```bash
docker compose config   # validate
docker compose build    # build backend + frontend images
docker compose up       # start
```

- **Frontend:** http://localhost:8080 (nginx)
- **Backend:** http://localhost:8000 (uvicorn, `/health` for readiness)
- Ports unchanged from the original setup. Backend mounts `./models` (read-only) and `./data` (SQLite persistence) and has a healthcheck against `/health`.

## Environment Variables

Copy `.env.example` to `.env` (git-ignored) and fill in values — **never commit secrets**:

| Variable | Purpose | Default when empty |
|---|---|---|
| `CORS_ALLOW_ORIGINS` | Extra allowed CORS origins | localhost:5173 defaults |
| `AUTH_SECRET_KEY` | Signs session tokens | Ephemeral per-process secret (warning logged) |
| `ADMIN_TOKEN` | Enables `/api/admin/stats` | Disabled (503) |
| `WEATHER_API_KEY` | OpenWeatherMap key (server-side only) | Weather returns "not configured" |
| `WEATHER_PROVIDER` | Force provider (`openweathermap`) | Auto from key presence |
| `AI_PROVIDER` | `knowledge_base` or `openai` | `knowledge_base` fallback |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | Optional AI provider (server-side only) | Knowledge base used |
| `APP_DB_PATH` | SQLite location | `data/app.db` |

## Local Execution Steps

**Backend**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt   # dev: pytest, httpx
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

**Retrain the model (optional)**
```bash
python -m src.data_preprocessing
python -m src.train          # logs to MLflow, rewrites models/*.pkl
```

## Testing

```bash
# Backend tests (19 tests): prediction, validation, history, assistant,
# weather fallback, recommendations, auth flow, admin guards, unit tests
.venv/bin/python -m pytest tests/ -q

# Frontend production build
cd frontend && npm run build

# Docker validation
docker compose config
```

Manual checks: `GET /health`, rice `POST /predict` → rice with confidence, `{}` → 422, language switcher, mobile viewport.

## Screenshots

> Placeholder — add screenshots here before publishing:
>
> - Home + prediction result (confidence, top-3, crop card)
> - Dashboard (stats, chart, history)
> - Assistant chat (EN / TE)
> - Weather (configured + not-configured states)
> - Login/Register modal
> - Mobile (Android) views

## Future Enhancements

- DVC remote + `dvc.yaml` stages; MLflow tracking server instead of local file store
- CI pipeline (pytest + build + Docker) — pytest suite is ready
- User-scoped dashboards and per-user model feedback loops
- Real-time weather alerts and forecast endpoints (multi-day)
- Federated/offline usage for low-connectivity rural areas
- Model retraining automation with drift-triggered schedules
