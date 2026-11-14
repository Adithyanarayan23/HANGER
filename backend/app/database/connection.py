from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from app.core.config import settings

DEFAULT_FALLBACK_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/hanger_db"

_engine: Optional[Engine] = None


def get_database_url() -> str:
    """Return configured DATABASE_URL or safe local PostgreSQL fallback format."""
    db_url = (settings.DATABASE_URL or "").strip()
    return db_url if db_url else DEFAULT_FALLBACK_DB_URL


def get_engine() -> Engine:
    """
    Lazily create and return the synchronous SQLAlchemy Engine.
    Note: create_engine() configures the dialect and connection pool lazily without
    opening a live TCP socket until .connect() or a query is executed.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
            echo=False,
        )
    return _engine


# Expose engine instance configured lazily (does not connect on import)
engine: Engine = get_engine()
