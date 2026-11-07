"""Database configuration for CompeteIQ backend.

Supports SQLite (local development) via DATABASE_URL, with a clear migration
path to PostgreSQL by changing DATABASE_URL to a PostgreSQL connection string.
"""
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger("competeiq.database")


class Base(DeclarativeBase):
    pass


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./competeiq.db")

# connect_args needed only for SQLite (check_same_thread allows use across threads)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and apply safe additive migrations.

    ``create_all`` handles brand-new tables (e.g. workflow_runs). Existing
    tables get newly-added columns through ``ALTER TABLE ... ADD COLUMN``
    which is safe on both SQLite and PostgreSQL (idempotent: columns are
    checked with PRAGMA/table inspection first).
    """
    # Import models so they are registered on Base.metadata
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_added_columns()


# Columns added after the initialCompeteIQ release, mapped as
# (table_name, [(column_name, column_type), ...]). Idempotent.
_ADDED_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "strategic_recommendations": [
        ("workflow_id", "VARCHAR(36) DEFAULT ''"),
        ("band_room_id", "VARCHAR(64) DEFAULT ''"),
        ("band_room_url", "VARCHAR(255) DEFAULT ''"),
        ("hindsight_memory_refs", "JSON DEFAULT '[]'"),
        ("hindsight_retained_at", "VARCHAR(64) DEFAULT ''"),
    ],
    "agent_messages": [
        ("workflow_id", "VARCHAR(36) DEFAULT ''"),
        ("band_message_id", "VARCHAR(64) DEFAULT ''"),
        ("band_sent_at", "VARCHAR(64) DEFAULT ''"),
        ("sender_name", "VARCHAR(200) DEFAULT ''"),
        ("direction", "VARCHAR(32) DEFAULT 'dispatch'"),
    ],
}


def _migrate_added_columns():
    """Add any missing columns from _ADDED_COLUMNS (idempotent, additive only)."""
    from sqlalchemy import inspect, text as sa_text

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in existing_tables:
                continue  # create_all already made it fresh with all columns
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            for col, ddl in columns:
                if col in existing_cols:
                    continue
                logger.info("Applying migration: ADD COLUMN %s.%s", table, col)
                conn.execute(sa_text(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {ddl}'))
