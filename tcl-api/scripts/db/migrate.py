#!/usr/bin/env python3
"""Alembic-style database migration script for ToneCards Lab API."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tcl_api.repository.db.database import engine


def create_alembic_config():
    """Create Alembic configuration if it doesn't exist."""
    project_root = Path(__file__).parent.parent.parent
    alembic_dir = project_root / "alembic"

    if not alembic_dir.exists():
        print("Creating Alembic configuration...")

        # Initialize Alembic
        os.chdir(project_root)
        alembic_cfg = Config()
        command.init(alembic_cfg, "alembic")

        # Update alembic.ini with our database URL
        ini_file = project_root / "alembic.ini"
        if ini_file.exists():
            content = ini_file.read_text()
            # Replace the sqlalchemy.url line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('sqlalchemy.url'):
                    lines[i] = f"sqlalchemy.url = {engine.url}"
                    break
            ini_file.write_text('\n'.join(lines))

        # Update env.py to import our models
        env_file = alembic_dir / "env.py"
        if env_file.exists():
            env_content = env_file.read_text()

            # Add imports
            imports = """
# Import your models here for autogenerate support
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tcl_api.repository.db.database import Base
from tcl_api.repository.db.models import (
    User, Deck, Card, DeckViewer, DeckInvitation,
    UploadedFile, ContentReport, DeckModeration,
    AuthToken, DeckStatistics
)
"""

            # Find the target_metadata line and replace it
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if 'target_metadata = None' in line:
                    lines[i] = 'target_metadata = Base.metadata'
                    break

            # Add imports at the top
            lines.insert(10, imports)

            env_file.write_text('\n'.join(lines))

        print("Alembic configuration created successfully")
        return project_root / "alembic.ini"

    return project_root / "alembic.ini"


def create_initial_migration():
    """Create initial migration from current models."""
    try:
        config_file = create_alembic_config()
        alembic_cfg = Config(config_file)

        print("Creating initial migration...")
        command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
        print("Initial migration created successfully")

    except Exception as e:
        print(f"Error creating migration: {e}")


def run_migrations():
    """Run all pending migrations."""
    try:
        config_file = Path(__file__).parent.parent.parent / "alembic.ini"
        if not config_file.exists():
            print("Alembic not initialized. Run create_initial_migration first.")
            return

        alembic_cfg = Config(config_file)

        print("Running migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully")

    except Exception as e:
        print(f"Error running migrations: {e}")


def show_migration_history():
    """Show migration history."""
    try:
        config_file = Path(__file__).parent.parent.parent / "alembic.ini"
        if not config_file.exists():
            print("Alembic not initialized.")
            return

        alembic_cfg = Config(config_file)
        command.history(alembic_cfg)

    except Exception as e:
        print(f"Error showing history: {e}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate.py init     - Initialize Alembic and create initial migration")
        print("  python migrate.py upgrade  - Run all pending migrations")
        print("  python migrate.py history  - Show migration history")
        print("  python migrate.py revision 'message'  - Create new migration")
        return

    action = sys.argv[1]

    if action == "init":
        create_initial_migration()
    elif action == "upgrade":
        run_migrations()
    elif action == "history":
        show_migration_history()
    elif action == "revision":
        if len(sys.argv) < 3:
            print("Please provide a migration message")
            return

        try:
            config_file = Path(__file__).parent.parent.parent / "alembic.ini"
            alembic_cfg = Config(config_file)
            command.revision(alembic_cfg, autogenerate=True, message=sys.argv[2])
            print(f"Migration '{sys.argv[2]}' created successfully")
        except Exception as e:
            print(f"Error creating migration: {e}")
    else:
        print(f"Unknown action: {action}")


if __name__ == "__main__":
    main()

