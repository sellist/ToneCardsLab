#!/usr/bin/env python3
"""Database creation and migration script for ToneCards Lab API."""

import os
import sys
import logging
from pathlib import Path
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tcl_api.repository.db.database import Base, engine, DB_TYPE, setup_database
from tcl_api.repository.db.models import (
    User, Deck, Card, DeckViewer, DeckInvitation,
    UploadedFile, ContentReport, DeckModeration,
    AuthToken, DeckStatistics, RendererType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_extensions():
    try:
        if DB_TYPE == "postgresql":
            with engine.connect() as conn:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                logger.info("Created uuid-ossp extension")

                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
                logger.info("Created pgcrypto extension")

                conn.commit()
        elif DB_TYPE in ("sqlite", "mysql"):
            logger.info(f"{DB_TYPE.capitalize()} doesn't require additional extensions for this schema")
        else:
            logger.warning(f"Extensions not configured for database type: {DB_TYPE}")

    except Exception as e:
        logger.error(f"Error creating extensions: {e}")
        raise


def main():
    try:
        logger.info(f"Starting {DB_TYPE} database setup...")

        setup_database()

        create_extensions()

        logger.info(f"{DB_TYPE} database setup completed successfully!")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

