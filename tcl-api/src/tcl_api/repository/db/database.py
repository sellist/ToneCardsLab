"""Database session management and configuration."""

import logging
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlmodel import SQLModel
from typing import Generator
from contextlib import contextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    database_url: str = "sqlite:///./tonecards.db"
    sql_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


db_settings = DatabaseSettings()
DATABASE_URL = db_settings.database_url


def _detect_database_type(url: str) -> str:
    if url.startswith("postgresql") or url.startswith("postgres"):
        return "postgresql"
    elif url.startswith("sqlite"):
        return "sqlite"
    else:
        return "unknown"


def _get_postgresql_engine_options():
    """Get PostgreSQL-specific engine options."""
    return {
        "pool_pre_ping": True,
        "echo": db_settings.sql_echo,
        "future": True
    }


def _get_sqlite_engine_options():
    """Get SQLite-specific engine options."""
    return {
        "echo": db_settings.sql_echo,
        "future": True,
        "connect_args": {"check_same_thread": False}
    }


DB_TYPE = _detect_database_type(DATABASE_URL)
if DB_TYPE == "postgresql":
    engine_options = _get_postgresql_engine_options()
elif DB_TYPE == "sqlite":
    engine_options = _get_sqlite_engine_options()
else:
    engine_options = {
        "pool_pre_ping": True,
        "echo": db_settings.sql_echo,
        "future": True
    }

engine = create_engine(DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    SQLModel.metadata.create_all(bind=engine)


def drop_db() -> None:
    SQLModel.metadata.drop_all(bind=engine)


def create_database_if_not_exists() -> bool:
    try:
        parsed_url = urlparse(DATABASE_URL)
        database_name = parsed_url.path.lstrip('/')

        if DB_TYPE == "postgresql":
            return _create_postgresql_database(parsed_url, database_name)
        elif DB_TYPE == "sqlite":
            return _create_sqlite_database(database_name)
        else:
            logger.warning(f"Database auto-creation not supported for {DB_TYPE}")
            return False

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False


def _create_postgresql_database(parsed_url, database_name: str) -> bool:
    try:
        # Create connection URL to postgres database
        base_url = f"postgresql://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}"
        if parsed_url.port:
            base_url += f":{parsed_url.port}"
        base_url += "/postgres"

        temp_engine = create_engine(base_url, **_get_postgresql_engine_options())

        with temp_engine.connect() as conn:
            # Set autocommit for database creation
            conn.execute(text("COMMIT"))

            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": database_name}
            )

            if not result.fetchone():
                logger.info(f"Creating PostgreSQL database '{database_name}'...")
                conn.execute(text(f'CREATE DATABASE "{database_name}"'))
                logger.info(f"PostgreSQL database '{database_name}' created successfully")
                return True
            else:
                logger.info(f"PostgreSQL database '{database_name}' already exists")
                return False

        temp_engine.dispose()

    except Exception as e:
        logger.error(f"Could not create PostgreSQL database: {e}")
        return False


def _create_sqlite_database(database_path: str) -> bool:
    try:
        import pathlib

        if database_path.startswith('./'):
            db_path = pathlib.Path(database_path)
        elif database_path.startswith('/'):
            db_path = pathlib.Path(database_path)
        else:
            db_path = pathlib.Path(database_path)

        db_path.parent.mkdir(parents=True, exist_ok=True)

        if db_path.exists():
            logger.info(f"SQLite database '{database_path}' already exists")
            return False
        else:
            logger.info(f"Creating SQLite database '{database_path}'...")
            from sqlalchemy import create_engine as ce
            temp_engine = ce(DATABASE_URL, **_get_sqlite_engine_options())
            temp_engine.dispose()
            logger.info(f"SQLite database '{database_path}' created successfully")
            return True

    except Exception as e:
        logger.error(f"Could not create SQLite database: {e}")
        return False


def setup_database() -> None:
    try:
        create_database_if_not_exists()

        init_db()

        logger.info("Database setup completed successfully")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
