# StockPulse Progress Tracker

## Phase 1: Week 1 — Data Pipeline & Feature Engineering

### 1. Setup Environment
- [x] Create a virtual environment — `venv/` exists
- [x] Install core packages — all dependencies defined in `pyproject.toml` (pandas, numpy, yfinance, requests, python-dotenv, sqlalchemy, psycopg2-binary, plus extras like transformers, xgboost, scikit-learn, mlflow, fastapi, uvicorn)
- [x] Set up a `.env` file for API keys and database credentials — `.env` and `.env.example` created with DATABASE_URL, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY, MLFLOW_TRACKING_URI
- [x] Initialize Git repo with `.gitignore` — repo initialized, `.gitignore` covers `.env`, `venv/`, `__pycache__/`, mlruns, data dirs, etc.
- [x] Project configuration system — `configs/base.yaml` with stock tickers, feature params, model splits, monitoring thresholds; `src/utils/config.py` with Pydantic settings loading from env + YAML
- [x] Structured logging — `src/utils/logging.py` with structlog (dev: colored console, prod: JSON output)

### 2. Stock Price Data Ingestion
- [ ] Register for a free financial data API
- [ ] Write a script to fetch daily OHLCV data via yfinance
- [ ] Fetch at least 1 year of historical data per stock
- [ ] Store raw data in `raw_stock_prices` table

### 3. Financial News Ingestion
- [ ] Fetch financial headlines per stock ticker via news API
- [ ] Extract relevant fields (ticker, headline, summary, source, published_date)
- [ ] Run sentiment analysis using FinBERT
- [ ] Store results in `raw_news_sentiment` table

### 4. Feature Engineering Pipeline
- [ ] Compute technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, volume change %)
- [ ] Aggregate daily news sentiment per ticker
- [ ] Create target variable (`price_direction`)
- [ ] Handle missing values
- [ ] Save feature matrix to `features` table
- [ ] Document features in `FEATURES.md`

### 5. Database Schema Design
- [x] Set up PostgreSQL via Docker — `docker/docker-compose.yaml` with Postgres 17, health checks, persistent volume
- [x] Design and create tables — `docker/init.sql` defines: `raw_stock_prices`, `raw_news_sentiment`, `features`, `predictions`, `model_registry`, `pipeline_runs`, `monitoring_logs` (extra tables beyond plan)
- [x] Schema includes indexes, unique constraints, auto-update triggers

---

## Phase 2: Week 2 — Model Training & Experiment Tracking
- [ ] Not started

## Phase 3: Week 3 — Pipeline Automation & API Deployment
- [ ] Not started

## Phase 4: Week 4 — Model Monitoring Dashboard
- [ ] Not started

---

## Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1 — Data Pipeline | In Progress | ~30% |
| Phase 2 — Model Training | Not Started | 0% |
| Phase 3 — API Deployment | Not Started | 0% |
| Phase 4 — Monitoring | Not Started | 0% |

**What's done:** Project scaffolding, environment setup, configuration system, structured logging, database schema, and Docker Compose for Postgres.

**Next up:** Stock price data ingestion script (Phase 1, Task 2).
