from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from functools import lru_cache
from src.utils.config import get_database_settings


@lru_cache(maxsize=1)
def get_session_factory():
    """Create and return a cached SQLAlchemy session factory.

    Returns:
        sqlalchemy.orm.sessionmaker: A session factory bound to a configured
            engine with connection pooling (pool_size=5, max_overflow=10)
            and pre-ping enabled.

    Note:
        The factory is cached via ``lru_cache``, so subsequent calls return
        the same instance without creating a new engine or connection pool.
    """
    url = get_database_settings().url
    engine = create_engine(
        url, pool_size=5, max_overflow=10, pool_pre_ping=True
    )

    return sessionmaker(bind=engine)


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
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
