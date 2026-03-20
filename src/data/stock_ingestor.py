import yfinance as yf
import pandas as pd
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    RetryCallState,
    retry_if_not_exception_type,
)

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from src.utils.logging import get_logger
from src.data.database import get_session
from src.data.models import RawStockPrice

logger = get_logger(__name__)


class EmptyStockDataError(Exception):
    """Raised when yfinance returns no data for a ticker/period combination.

    This can happen when a ticker is delisted, the period is invalid,
    or yfinance has no data for the requested range.
    """

    pass


def _log_retry(retry_state: RetryCallState) -> None:
    """Log a warning before tenacity sleeps between retry attempts.

    Called automatically by tenacity via the `before_sleep` hook.

    Args:
        retry_state: Tenacity's state object for the current retry cycle,
            containing the attempt number and the exception that triggered
            the retry.
    """
    logger.warning(
        "retrying_stock_download",
        attempt=retry_state.attempt_number,
        exception=str(retry_state.outcome.exception()),
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=_log_retry,
    retry=retry_if_not_exception_type(EmptyStockDataError),
)
def extract_stock_data(ticker: str, lookback_days: int) -> pd.DataFrame:
    """Download raw OHLCV data for a ticker from yfinance.

    Retries up to 3 times on network/API failures with exponential backoff
    (4s, 8s). Does not retry on EmptyStockDataError — that indicates a data
    availability issue, not a transient failure.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".
        lookback_days: Number of calendar days of history to fetch.

    Returns:
        DataFrame with a MultiIndex column structure (Price, Ticker) and
        a DatetimeIndex. Columns include Close, High, Low, Open, Volume.

    Raises:
        EmptyStockDataError: If yfinance returns a non-empty response but
            with no rows — e.g. delisted ticker or invalid period.
        tenacity.RetryError: If all 3 attempts fail due to network/API errors.
    """
    df = yf.download(ticker, period=f"{lookback_days}d", interval="1d")

    if df.empty:
        logger.warning(
            "empty_stock_data", ticker=ticker, lookback_days=lookback_days
        )
        raise EmptyStockDataError(
            f"No data returned for {ticker} over {lookback_days}d"
        )

    logger.info(
        "stock_data_extracted",
        ticker=ticker,
        lookback_days=lookback_days,
        rows=len(df),
    )
    return df


def transform_stock_data(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Normalize raw yfinance output into a flat, database-ready DataFrame.

    Performs the following transformations:
    - Drops the "Ticker" level from the MultiIndex columns, leaving only
    the price field names (Close, High, Low, Open, Volume).
    - Resets the DatetimeIndex so Date becomes a plain column.
    - Converts Date to a Python date object (strips time component).
    - Renames columns to snake_case to match the RawStockPrice model.
    - Adds "ticker" and "data_source" columns.

    Args:
        df: Raw DataFrame returned by extract_stock_data().
        ticker: Stock ticker symbol, e.g. "AAPL". Stored as a column value.

    Returns:
        Flat DataFrame with columns: date, open, high, low, close, volume,
        ticker, data_source.
    """
    df = df.copy()
    df.columns = df.columns.droplevel("Ticker")
    df = df.reset_index()
    df["ticker"] = ticker
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["data_source"] = "yfinance"
    df.columns.name = (
        None  # Remove the column name (e.g., "Price") from the columns index
    )
    df.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        },
        inplace=True,
    )
    return df

def load_stock_data(df: pd.DataFrame) -> None:
    """Upsert transformed stock data into the raw_stock_prices table.

    Uses a PostgreSQL INSERT ... ON CONFLICT DO UPDATE so re-running the
    pipeline with overlapping date ranges is safe — existing rows are updated
    with the latest values rather than causing duplicate key errors.

    On conflict (ticker, date), updates OHLCV and data_source but leaves
    id, ticker, date, and created_at untouched.

    Args:
        df: Transformed DataFrame from transform_stock_data(), expected to
            have columns: ticker, date, open, high, low, close, volume,
            data_source.
    """
    records = df.to_dict(orient="records")

    stmt = insert(RawStockPrice).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint="unique_ticker_date",
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
            "data_source": stmt.excluded.data_source,
            "updated_at": func.now(),
        },
    )

    with get_session() as session:
        session.execute(stmt)

    logger.info("stock_data_loaded", rows=len(records))
