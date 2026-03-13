## 🗺️ Project Roadmap & Task List

### Phase 1: Week 1 — Data Pipeline & Feature Engineering

_Goal: Build automated data ingestion and a feature engineering pipeline that pulls stock data + news sentiment into a clean PostgreSQL schema._

- [ ] **1. Setup Environment:**
  - [ ] Create a virtual environment (`python -m venv venv`).
  - [ ] Install core packages: `pandas`, `numpy`, `yfinance`, `requests`, `python-dotenv`, `sqlalchemy`, `psycopg2-binary`.
  - [ ] Set up a `.env` file for API keys and database credentials.
  - [ ] Initialize Git repo with `.gitignore` (include `.env`, `venv/`, `__pycache__/`).
- [ ] **2. Stock Price Data Ingestion:**
  - [ ] Register for a free financial data API (Alpha Vantage, Finnhub, or Polygon.io).
  - [ ] Write a script using `yfinance` to fetch daily OHLCV (Open, High, Low, Close, Volume) data for a list of target stocks (e.g., AAPL, GOOGL, MSFT, TSLA).
  - [ ] Fetch at least 1 year of historical data per stock.
  - [ ] Store raw data in a Pandas DataFrame and save to a `raw_stock_prices` table in PostgreSQL.
- [ ] **3. Financial News Ingestion:**
  - [ ] Use a free news API (Finnhub News, Alpha Vantage News Sentiment, or NewsAPI) to fetch recent financial headlines per stock ticker.
  - [ ] Extract relevant fields: `ticker`, `headline`, `summary`, `source`, `published_date`.
  - [ ] Run sentiment analysis on each headline/summary using a pre-trained model (`transformers` pipeline with `finbert` or `textblob` as fallback).
  - [ ] Store results in a `raw_news_sentiment` table with columns: `ticker`, `headline`, `sentiment_score`, `sentiment_label`, `published_date`.
- [ ] **4. Feature Engineering Pipeline:**
  - [ ] Write a modular `feature_engineering.py` script that:
    - [ ] Computes technical indicators: SMA (7, 21, 50-day), EMA (12, 26), RSI (14-day), MACD, Bollinger Bands, daily volume change %.
    - [ ] Aggregates daily news sentiment per ticker: mean sentiment, count of positive/negative articles, max sentiment swing.
    - [ ] Creates the target variable: `price_direction` (1 = next-day close > today's close, 0 = otherwise).
    - [ ] Handles missing values (forward-fill for price gaps, zero-fill for days with no news).
  - [ ] Save the final feature matrix to a `features` table in PostgreSQL.
  - [ ] Document each feature in a `FEATURES.md` file (name, description, calculation method).
- [ ] **5. Database Schema Design:**
  - [ ] Set up PostgreSQL locally (or use Docker: `docker run -p 5432:5432 -e POSTGRES_PASSWORD=pwd postgres`).
  - [ ] Design and create tables: `raw_stock_prices`, `raw_news_sentiment`, `features`, `predictions`, `model_registry`.
  - [ ] Write a `schema.sql` or use SQLAlchemy models for schema management.

### Phase 2: Week 2 — Model Training & Experiment Tracking

_Goal: Train a stock direction classifier, track experiments systematically, and establish a baseline model._

- [ ] **1. MLflow Setup:**
  - [ ] Install MLflow (`pip install mlflow`).
  - [ ] Start the MLflow tracking server locally (`mlflow server --host 0.0.0.0 --port 5000`).
  - [ ] Configure tracking URI in your project settings.
  - [ ] Create an MLflow experiment named `stockpulse-direction-prediction`.
- [ ] **2. Data Preparation:**
  - [ ] Write a `data_loader.py` module to:
    - [ ] Pull feature data from PostgreSQL.
    - [ ] Split into train/validation/test sets using time-based splitting (e.g., train: first 8 months, val: next 2 months, test: last 2 months). **Never use random split for time-series data.**
    - [ ] Apply feature scaling (StandardScaler or MinMaxScaler) — fit on train, transform on val/test.
    - [ ] Handle class imbalance if present (SMOTE or class weights).
- [ ] **3. Baseline Model:**
  - [ ] Train a simple Logistic Regression as baseline.
  - [ ] Log to MLflow: hyperparameters, accuracy, precision, recall, F1-score, confusion matrix.
  - [ ] Save the baseline metrics for comparison.
- [ ] **4. Primary Model Training:**
  - [ ] Train an XGBoost classifier (`pip install xgboost`).
  - [ ] Perform hyperparameter tuning using `GridSearchCV` or `Optuna`:
    - [ ] Tune: `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`.
  - [ ] Log each experiment run to MLflow:
    - [ ] Hyperparameters.
    - [ ] Evaluation metrics: accuracy, precision, recall, F1, ROC-AUC.
    - [ ] Feature importance plot (save as artifact).
    - [ ] Confusion matrix (save as artifact).
    - [ ] Training data version/date range.
  - [ ] Optionally try a RandomForest and LightGBM for comparison.
- [ ] **5. Model Registration:**
  - [ ] Register the best model in MLflow Model Registry.
  - [ ] Tag it with version, training date, and data date range.
  - [ ] Save model metadata to the `model_registry` table in PostgreSQL (model_id, model_type, metrics_json, training_date, data_start, data_end, status).
  - [ ] Write a `model_selector.py` that retrieves the current "production" model.
- [ ] **6. Evaluation Report:**
  - [ ] Generate a classification report for the best model.
  - [ ] Create a feature importance ranking.
  - [ ] Document findings in a `MODEL_REPORT.md`.

### Phase 3: Week 3 — Pipeline Automation & API Deployment

_Goal: Automate the entire fetch → feature → predict pipeline and serve predictions via a REST API._

- [ ] **1. Pipeline Orchestration:**
  - [ ] Write a `pipeline.py` module with distinct stages:
    - [ ] `fetch_data()` — pulls latest stock prices and news.
    - [ ] `generate_features()` — runs feature engineering on new data.
    - [ ] `run_predictions()` — loads production model, generates predictions, saves to `predictions` table.
    - [ ] `evaluate_predictions()` — compares yesterday's predictions with actual outcomes, logs accuracy.
  - [ ] Add error handling and logging (`logging` module) at each stage.
- [ ] **2. Scheduling & Automation:**
  - [ ] **Option A (Simple):** Use `APScheduler` to run the pipeline daily after market close.
  - [ ] **Option B (Production-grade):** Set up Apache Airflow with a DAG that chains the pipeline stages.
    - [ ] Install Airflow (`pip install apache-airflow`).
    - [ ] Write an Airflow DAG: `stockpulse_daily_dag.py`.
    - [ ] Define tasks for each pipeline stage with dependencies.
  - [ ] Add a weekly retraining task that:
    - [ ] Retrains the model on the latest data window.
    - [ ] Logs the new run to MLflow.
    - [ ] Promotes to production if metrics improve over current model.
- [ ] **3. FastAPI Prediction Service:**
  - [ ] Install FastAPI and Uvicorn (`pip install fastapi uvicorn`).
  - [ ] Create API endpoints:
    - [ ] `GET /api/predictions/?ticker=AAPL` — Returns latest predictions for a stock.
    - [ ] `GET /api/predictions/history?ticker=AAPL&days=30` — Returns prediction history.
    - [ ] `GET /api/model/info` — Returns current model metadata (version, metrics, training date).
    - [ ] `GET /api/model/performance` — Returns rolling accuracy of predictions vs actuals.
    - [ ] `GET /api/features/?ticker=AAPL` — Returns latest feature values.
  - [ ] Add input validation with Pydantic schemas.
  - [ ] Add basic error handling and response models.
- [ ] **4. Dockerization:**
  - [ ] Write a `Dockerfile` for the FastAPI service.
  - [ ] Write a `docker-compose.yml` that runs:
    - [ ] PostgreSQL database.
    - [ ] FastAPI prediction service.
    - [ ] MLflow tracking server.
    - [ ] Pipeline scheduler (APScheduler or Airflow).
  - [ ] Test that `docker-compose up` spins up the full system.

### Phase 4: Week 4 — Model Monitoring Dashboard

_Goal: Build a monitoring dashboard that tracks model health, detects drift, and visualizes performance over time._

- [ ] **1. Monitoring Backend Logic:**
  - [ ] Write a `monitoring.py` module that computes:
    - [ ] Daily prediction accuracy (predicted direction vs actual).
    - [ ] Rolling 7-day and 30-day accuracy.
    - [ ] Feature distribution statistics (mean, std, skew) for current window vs training window.
    - [ ] Data drift score using a simple method (Population Stability Index or KS test).
    - [ ] Alerts: flag if rolling accuracy drops below a threshold (e.g., < 52%) or drift score exceeds threshold.
  - [ ] Store monitoring metrics in a `monitoring_logs` table.
- [ ] **2. Dashboard UI (Streamlit):**
  - [ ] Install Streamlit (`pip install streamlit`).
  - [ ] Build dashboard pages:
    - [ ] **Overview:** Current model version, overall accuracy, last training date, next scheduled retraining, system status (healthy / degraded / alert).
    - [ ] **Prediction Accuracy:** Line chart of daily accuracy over last 30/60/90 days with a baseline threshold line.
    - [ ] **Feature Drift:** Heatmap or bar chart showing drift scores per feature, color-coded by severity.
    - [ ] **Feature Importance:** Bar chart comparing current vs training-time feature importances.
    - [ ] **Prediction Log:** Searchable table of recent predictions with actual outcomes and correctness.
    - [ ] **Retraining History:** Table of past model versions with their metrics, linked to MLflow runs.
  - [ ] Add a manual "Retrain Now" button that triggers the retraining pipeline.
  - [ ] Add ticker selection dropdown to filter all views by stock.
- [ ] **3. Alerting (Optional but Impressive):**
  - [ ] Set up simple email or Slack alerts when:
    - [ ] Model accuracy drops below threshold.
    - [ ] Data drift is detected.
    - [ ] Pipeline fails to run.
  - [ ] Use `smtplib` for email or a Slack webhook for notifications.
- [ ] **4. Documentation & README:**
  - [ ] Write a comprehensive `README.md`:
    - [ ] Project overview and architecture diagram.
    - [ ] Setup instructions (local + Docker).
    - [ ] API documentation with example requests/responses.
    - [ ] Screenshots of the monitoring dashboard.
    - [ ] Tech stack summary.
  - [ ] Add an architecture diagram (use draw.io or Mermaid).
  - [ ] Record a short demo video or GIF (optional but highly recommended for portfolio).
