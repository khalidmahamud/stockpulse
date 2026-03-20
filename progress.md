# StockPulse — Project Progress & Context

> **Purpose of this document:** This is a self-contained context file. Any LLM reading this should be able to understand the entire project state, architecture, schema, decisions made, and what to build next.

---

## 1. Project Overview

**StockPulse** is an end-to-end stock prediction pipeline that:
1. Ingests daily stock prices (yfinance) and financial news (Finnhub/Alpha Vantage)
2. Runs sentiment analysis on news using FinBERT
3. Engineers technical indicator features + sentiment features
4. Trains an XGBoost classifier to predict next-day price direction (up/down)
5. Serves predictions via a FastAPI REST API
6. Monitors model health (accuracy drift, feature drift) via a Streamlit dashboard

**Author:** Khalid Mahamud
**Python:** >=3.10
**Build system:** Hatchling (`pyproject.toml`)
**License:** MIT

---

## 2. Directory Structure

```
stockpulse/
├── configs/
│   └── base.yaml              # Central YAML config (tickers, feature params, model splits, thresholds)
├── docker/
│   ├── docker-compose.yaml    # Postgres 17 service with health checks
│   └── init.sql               # Full DB schema (7 tables, indexes, triggers)
├── docs/                      # (empty — reserved for future docs)
├── scripts/                   # (empty — reserved for CLI/run scripts)
├── tests/                     # (empty — reserved for pytest tests)
├── src/
│   ├── __init__.py
│   ├── api/
│   │   └── __init__.py        # (empty — FastAPI endpoints go here, Phase 3)
│   ├── data/
│   │   ├── __init__.py
│   │   └── database.py        # SQLAlchemy engine + session context manager
│   ├── features/
│   │   └── __init__.py        # (empty — feature engineering pipeline, Phase 1)
│   ├── models/
│   │   └── __init__.py        # (empty — model training/selection, Phase 2)
│   ├── monitoring/
│   │   └── __init__.py        # (empty — drift detection/alerting, Phase 4)
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # Pydantic settings + YAML config loader
│       └── logging.py          # structlog setup (dev: colored console, prod: JSON)
├── .env                        # Real secrets (git-ignored)
├── .env.example                # Template for env vars
├── .gitignore                  # Comprehensive ignore list
├── pyproject.toml              # All dependencies, tool config (black, ruff, mypy, pytest)
├── Makefile                    # (empty — reserved for convenience commands)
├── README.md                   # (empty — Phase 4 deliverable)
├── plan.md                     # Full 4-phase roadmap with detailed task checklists
└── progress.md                 # This file
```

---

## 3. Tech Stack & Dependencies

| Category | Technology | Purpose |
|----------|-----------|---------|
| Data ingestion | `yfinance` | Daily OHLCV stock data |
| Data ingestion | `requests` | Finnhub/Alpha Vantage news API calls |
| Sentiment | `transformers` + `torch` | FinBERT model for headline sentiment |
| Features | `pandas`, `numpy` | Technical indicator computation |
| ML | `xgboost`, `scikit-learn` | Classification model + preprocessing |
| Experiment tracking | `mlflow` | Track runs, metrics, model registry |
| Database | PostgreSQL 17 (Docker) | All persistent storage |
| ORM | `sqlalchemy` + `psycopg2-binary` | DB connections and queries |
| API | `fastapi` + `uvicorn` | Prediction REST API |
| Config | `pydantic-settings`, `pyyaml` | Type-safe settings from env + YAML |
| Logging | `structlog` | Structured logging (JSON in prod) |
| Retry | `tenacity` | Resilient API calls |
| Dev tools | `pytest`, `black`, `ruff`, `mypy`, `pre-commit` | Testing, formatting, linting |

---

## 4. Database Schema (PostgreSQL)

Schema is defined in `docker/init.sql` and auto-applied on first `docker-compose up`.

### 4.1 `raw_stock_prices`
Stores daily OHLCV data per ticker from yfinance.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| ticker | VARCHAR(10) | NOT NULL |
| date | DATE | NOT NULL |
| open | NUMERIC(12,4) | |
| high | NUMERIC(12,4) | |
| low | NUMERIC(12,4) | |
| close | NUMERIC(12,4) | |
| adj_close | NUMERIC(12,4) | |
| volume | BIGINT | |
| data_source | VARCHAR(50) | Default: 'yfinance' |
| created_at | TIMESTAMPTZ | Auto |
| updated_at | TIMESTAMPTZ | Auto-updated via trigger |

- **Unique constraint:** `(ticker, date)`
- **Index:** `(ticker, date DESC)`
- **Trigger:** `update_updated_at_column()` auto-updates `updated_at` on row update

### 4.2 `raw_news_sentiment`
Stores news headlines with pre-computed sentiment scores.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| ticker | VARCHAR(10) | NOT NULL |
| headline | TEXT | NOT NULL |
| summary | TEXT | |
| source | VARCHAR(100) | |
| url | TEXT | |
| published_date | TIMESTAMPTZ | NOT NULL |
| sentiment_score | NUMERIC(5,4) | Range: -1.0 to 1.0 |
| sentiment_label | VARCHAR(20) | positive/negative/neutral |
| sentiment_model | VARCHAR(50) | Default: 'finbert' |
| created_at | TIMESTAMPTZ | Auto |

- **Unique constraint:** `(ticker, headline, published_date)`
- **Index:** `(ticker, published_date DESC)`

### 4.3 `features`
Computed feature matrix for model training — one row per ticker per date.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| ticker | VARCHAR(10) | NOT NULL |
| date | DATE | NOT NULL |
| sma_7, sma_21, sma_50 | NUMERIC(12,4) | Simple Moving Averages |
| ema_12, ema_26 | NUMERIC(12,4) | Exponential Moving Averages |
| rsi_14 | NUMERIC(8,4) | Relative Strength Index |
| macd, macd_signal, macd_histogram | NUMERIC(12,6) | MACD components |
| bollinger_upper/lower/middle | NUMERIC(12,4) | Bollinger Bands |
| volume_change_pct | NUMERIC(10,4) | Daily volume % change |
| sentiment_mean/max/min | NUMERIC(5,4) | Daily sentiment aggregations |
| news_count_positive/negative/neutral | INTEGER | Article counts by sentiment |
| price_direction | INTEGER | **Target:** 1=up, 0=down |
| feature_version | VARCHAR(20) | Default: 'v1' |
| created_at | TIMESTAMPTZ | Auto |

- **Unique constraint:** `(ticker, date)`
- **Index:** `(ticker, date DESC)`

### 4.4 `predictions`
Stores model predictions and actual outcomes for evaluation.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| ticker | VARCHAR(10) | NOT NULL |
| prediction_date | DATE | NOT NULL |
| predicted_direction | INTEGER | 1=up, 0=down |
| confidence | NUMERIC(5,4) | Model probability |
| model_id | VARCHAR(100) | NOT NULL |
| actual_direction | INTEGER | Filled after market close |
| is_correct | BOOLEAN | Computed after actual known |
| created_at | TIMESTAMPTZ | Auto |
| evaluated_at | TIMESTAMPTZ | When actual was filled |

- **Unique constraint:** `(ticker, prediction_date, model_id)`
- **Indexes:** `(ticker, prediction_date DESC)`, `(model_id, prediction_date DESC)`

### 4.5 `model_registry`
Tracks model versions and their lifecycle (staging → production → archived).

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| model_id | VARCHAR(100) | UNIQUE, NOT NULL |
| model_type | VARCHAR(50) | xgboost, random_forest, etc. |
| mlflow_run_id | VARCHAR(100) | Link to MLflow |
| metrics | JSONB | {accuracy, precision, recall, f1, roc_auc} |
| hyperparameters | JSONB | Full hyperparams dict |
| feature_version | VARCHAR(20) | |
| training_data_start | DATE | |
| training_data_end | DATE | |
| status | VARCHAR(20) | staging / production / archived |
| created_at | TIMESTAMPTZ | Auto |
| promoted_at | TIMESTAMPTZ | When moved to production |

- **Index:** `(status)`

### 4.6 `pipeline_runs`
Audit log for every pipeline execution.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| run_id | VARCHAR(100) | UNIQUE, NOT NULL |
| pipeline_stage | VARCHAR(50) | fetch_data / generate_features / run_predictions |
| status | VARCHAR(20) | running / success / failed |
| started_at | TIMESTAMPTZ | NOT NULL |
| completed_at | TIMESTAMPTZ | |
| rows_processed | INTEGER | |
| error_message | TEXT | |
| metadata | JSONB | |

- **Index:** `(pipeline_stage, started_at DESC)`

### 4.7 `monitoring_logs`
Stores daily monitoring metrics (accuracy, drift scores, alerts).

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| date | DATE | NOT NULL |
| metric_name | VARCHAR(50) | daily_accuracy, drift_score, etc. |
| metric_value | NUMERIC(10,6) | |
| ticker | VARCHAR(10) | NULL for overall metrics |
| details | JSONB | |
| created_at | TIMESTAMPTZ | Auto |

- **Indexes:** `(date DESC)`, `(metric_name, date DESC)`

---

## 5. Configuration System

### 5.1 Environment Variables (`.env`)
```
DATABASE_URL=postgresql://stockpulse:stockpulse_dev@localhost:5432/stockpulse
FINNHUB_API_KEY=<key>
ALPHA_VANTAGE_API_KEY=<key>
MLFLOW_TRACKING_URI=http://localhost:5000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 5.2 YAML Config (`configs/base.yaml`)
```yaml
stocks:
  tickers: [AAPL, GOOGL, MSFT, TSLA]
  lookback_days: 365

news:
  max_articles_per_ticker: 50
  sentiment_model: "ProsusAI/finbert"

features:
  sma_windows: [7, 21, 50]
  ema_windows: [12, 26]
  rsi_window: 14
  bollinger_window: 20
  bollinger_std: 2

model:
  train_split_ratio: 0.7
  validation_split_ratio: 0.15
  test_split_ratio: 0.15
  random_state: 42

monitoring:
  accuracy_threshold: 0.52
  drift_threshold: 0.1
  rolling_window_days: 30

api:
  host: "0.0.0.0"
  port: 8000
```

### 5.3 Config Access Pattern (`src/utils/config.py`)
- `DatabaseSettings`, `APIKeySettings`, `AppSettings` — Pydantic models loading from env vars
- `load_yaml_config()` — reads YAML from `configs/`
- `get_settings()` — cached function returning `{"database": ..., "api_keys": ..., "app": ..., "config": ...}`

---

## 6. Existing Code (What's Implemented)

### `src/utils/config.py` — Configuration management
- Pydantic `BaseSettings` classes for database, API keys, app settings
- YAML config loader for `configs/base.yaml`
- `get_settings()` cached function combining all settings

### `src/utils/logging.py` — Structured logging
- `setup_logging()` — call once at startup
- `get_logger(name)` — returns structlog bound logger
- Dev mode: colored console output. Prod mode: JSON output
- Usage: `logger = get_logger(__name__)` then `logger.info("event", key=value)`

### `src/data/database.py` — Database connectivity
- `get_engine()` — cached SQLAlchemy engine (pool_size=5, max_overflow=10, pre_ping=True)
- `get_session()` — context manager yielding a session with auto-commit/rollback
- Usage: `with get_session() as session: session.query(...)`

### Docker (`docker/docker-compose.yaml` + `docker/init.sql`)
- Postgres 17 container named `stockpulse_db`
- Credentials: `stockpulse / stockpulse_dev`
- DB name: `stockpulse`
- Port: 5432
- Persistent volume: `postgres_data`
- Health check: `pg_isready` every 5s
- Schema auto-applied via init.sql on first run

---

## 7. Key Design Decisions

1. **Time-series data splitting** — Train/val/test splits MUST be time-based (chronological), never random. Ratios: 70/15/15.
2. **Sentiment model** — Using `ProsusAI/finbert` (finance-specific BERT), not generic TextBlob.
3. **Target variable** — Binary classification: `price_direction` = 1 if next-day close > today's close, else 0.
4. **Feature versioning** — `feature_version` column in the `features` table allows schema evolution without breaking old data.
5. **Model lifecycle** — Models go through `staging → production → archived` in `model_registry`.
6. **Raw SQL schema** — Using raw SQL in `init.sql` (not SQLAlchemy ORM models). Database.py uses SQLAlchemy Core/session for queries only.
7. **No ORM models defined yet** — The project uses raw SQL for schema creation and SQLAlchemy sessions for queries. ORM model classes (declarative base) have NOT been created yet. You may need to decide: continue with raw SQL queries or add SQLAlchemy ORM models.
8. **Monitoring thresholds** — Alert if rolling accuracy < 52% or drift score > 0.1.
9. **Docker for DB only (so far)** — Full dockerization (API, MLflow, scheduler) is a Phase 3 task.

---

## 8. Phase Completion Status

| Phase | Description | Status | Completion |
|-------|-------------|--------|------------|
| Phase 1 | Data Pipeline & Feature Engineering | **In Progress** | ~30% |
| Phase 2 | Model Training & Experiment Tracking | Not Started | 0% |
| Phase 3 | Pipeline Automation & API Deployment | Not Started | 0% |
| Phase 4 | Model Monitoring Dashboard | Not Started | 0% |

### Phase 1 — Detailed Task Status

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Setup Environment | **Done** | venv, pyproject.toml, .env, .gitignore, config system, structured logging |
| 2 | Stock Price Data Ingestion | **Not Started** | Need: yfinance fetch script, store to `raw_stock_prices` |
| 3 | Financial News Ingestion | **Not Started** | Need: news API fetch, FinBERT sentiment, store to `raw_news_sentiment` |
| 4 | Feature Engineering Pipeline | **Not Started** | Need: technical indicators, sentiment aggregation, target var, store to `features` |
| 5 | Database Schema Design | **Done** | Full schema in `docker/init.sql`, 7 tables with indexes and triggers |

---

## 9. What To Build Next (In Order)

### Immediate: Phase 1, Task 2 — Stock Price Data Ingestion
**Create `src/data/stock_ingestor.py`** (or similar):
1. Read tickers from config (`configs/base.yaml` → `stocks.tickers`)
2. Use `yfinance.download()` to fetch 1 year of daily OHLCV data per ticker
3. Clean the DataFrame (handle multi-index from yfinance, rename columns to match schema)
4. Insert into `raw_stock_prices` table using SQLAlchemy session (upsert on `ticker, date` conflict)
5. Log progress with structlog
6. Add retry logic with `tenacity` for API failures

### Then: Phase 1, Task 3 — Financial News Ingestion
**Create `src/data/news_ingestor.py`**:
1. Fetch headlines from Finnhub or Alpha Vantage news API (using API keys from config)
2. Run each headline through FinBERT (`transformers` pipeline) for sentiment
3. Store in `raw_news_sentiment` table

### Then: Phase 1, Task 4 — Feature Engineering
**Create `src/features/feature_engineering.py`**:
1. Pull raw price data from `raw_stock_prices`
2. Compute: SMA(7,21,50), EMA(12,26), RSI(14), MACD, Bollinger Bands, volume change %
3. Pull and aggregate daily sentiment from `raw_news_sentiment`
4. Create target variable: `price_direction`
5. Handle missing values (forward-fill prices, zero-fill missing news days)
6. Save to `features` table

### After Phase 1: See `plan.md` for Phases 2-4 detailed tasks.

---

## 10. How to Run

```bash
# 1. Start the database
cd docker && docker-compose up -d

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Copy and fill in env vars
cp .env.example .env
# Edit .env with real API keys and DB credentials

# 5. Verify DB connection
python -c "from src.data.database import get_engine; print(get_engine().connect())"
```

---

## 11. Git History

```
abaeb1b  added database.py
85b54ff  Initial project structure
```

Two commits total. The project is in early stages. Branch: `master`. Main branch: `main`.
