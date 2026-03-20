from decimal import Decimal
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RawStockPrice(Base):
    __tablename__ = "raw_stock_prices"

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="unique_ticker_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[date] = mapped_column(nullable=False)
    open: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    close: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    adj_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    data_source: Mapped[Optional[str]] = mapped_column(
        String(50), server_default="yfinance"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        server_default=func.now()
    )
