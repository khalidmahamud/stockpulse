from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from functools import lru_cache
from src.utils.config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    """Create and return a cached SQLAlchemy engine.

    Returns:
        sqlalchemy.engine.Engine: A configured engine instance with connection
            pooling (pool_size=5, max_overflow=10) and pre-ping enabled.

    Note:
        The engine is cached via ``lru_cache``, so subsequent calls return the
        same instance without creating a new connection pool.
    """
    url = get_settings()["database"].url
    engine = create_engine(
        url, pool_size=5, max_overflow=10, pool_pre_ping=True
    )
    return engine


@contextmanager
def get_session():
    """Provide a transactional database session as a context manager.

    Yields:
        sqlalchemy.orm.Session: A scoped session bound to the cached engine.

    The session automatically commits on successful exit and rolls back on any
    exception. It is always closed when the block exits.

    Example::

        with get_session() as session:
            user = session.query(User).filter_by(id=1).first()
            user.name = "Alice"
        # Transaction is committed here if no exception was raised.
    """
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)

    session = session_factory()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
