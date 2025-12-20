#!/usr/bin/env python3

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tcl_api.repository.db.database import Base, engine
from tcl_api.repository.db.models import (
    User, Deck, Card, DeckViewer, DeckInvitation,
    UploadedFile, ContentReport, DeckModeration,
    AuthToken, DeckStatistics
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database management utilities."""

    def __init__(self):
        self.engine = engine
        self.inspector = inspect(engine)

    def create_tables(self, drop_existing=False):
        """Create all tables."""
        try:
            if drop_existing:
                logger.warning("Dropping all existing tables...")
                Base.metadata.drop_all(bind=self.engine)
                logger.info("All tables dropped")

            logger.info("Creating all tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("All tables created successfully")

        except Exception as e:
            logger.error(f"Error managing tables: {e}")
            raise

    def drop_tables(self):
        """Drop all tables."""
        try:
            logger.warning("Dropping all tables...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped")

        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise

    def list_tables(self):
        """List all tables in the database."""
        try:
            tables = self.inspector.get_table_names()
            logger.info(f"Tables in database: {', '.join(tables) if tables else 'None'}")
            return tables

        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def get_table_info(self, table_name):
        """Get detailed information about a specific table."""
        try:
            if not self.inspector.has_table(table_name):
                logger.error(f"Table '{table_name}' does not exist")
                return None

            columns = self.inspector.get_columns(table_name)
            indexes = self.inspector.get_indexes(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            primary_key = self.inspector.get_primary_keys(table_name)

            info = {
                'columns': columns,
                'indexes': indexes,
                'foreign_keys': foreign_keys,
                'primary_key': primary_key
            }

            logger.info(f"Table '{table_name}' info retrieved")
            return info

        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return None

    def backup_schema(self, output_file=None):
        """Generate SQL DDL for the current schema."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"schema_backup_{timestamp}.sql"

        try:
            # This is a simplified backup - in production you'd use pg_dump
            with open(output_file, 'w') as f:
                f.write("-- ToneCards Lab Database Schema Backup\n")
                f.write(f"-- Generated on: {datetime.now()}\n\n")

                # Write CREATE TABLE statements
                from sqlalchemy.schema import CreateTable
                for table in Base.metadata.sorted_tables:
                    create_sql = str(CreateTable(table).compile(self.engine))
                    f.write(f"{create_sql};\n\n")

            logger.info(f"Schema backup saved to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error creating schema backup: {e}")
            return None

    def check_database_health(self):
        """Perform database health checks."""
        try:
            logger.info("Performing database health check...")

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")

            # Check tables exist
            expected_tables = {
                'users', 'decks', 'cards', 'deck_viewers', 'deck_invitations',
                'uploaded_files', 'content_reports', 'deck_moderation',
                'auth_tokens', 'deck_statistics'
            }

            actual_tables = set(self.inspector.get_table_names())
            missing_tables = expected_tables - actual_tables

            if missing_tables:
                logger.error(f"✗ Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("✓ All expected tables present")

            # Check foreign key constraints
            fk_issues = []
            for table_name in expected_tables:
                if table_name in actual_tables:
                    fks = self.inspector.get_foreign_keys(table_name)
                    for fk in fks:
                        ref_table = fk['referred_table']
                        if ref_table not in actual_tables:
                            fk_issues.append(f"{table_name} -> {ref_table}")

            if fk_issues:
                logger.error(f"✗ Foreign key issues: {', '.join(fk_issues)}")
                return False
            else:
                logger.info("✓ Foreign key constraints valid")

            # Check if database is empty or has data
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                logger.info(f"✓ Database contains {user_count} users")

            logger.info("Database health check completed successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Database health check failed: {e}")
            return False

    def seed_sample_data(self):
        """Insert sample data for testing."""
        try:
            logger.info("Seeding sample data...")

            from tcl_api.repository.db.database import get_db_context

            with get_db_context() as db:
                # Check if data already exists
                existing_users = db.query(User).count()
                if existing_users > 0:
                    logger.info(f"Database already contains {existing_users} users, skipping seed")
                    return

                # Create sample user
                sample_user = User(
                    email="test@example.com",
                    name="Test User",
                    preferences={"theme": "dark", "language": "en"}
                )
                db.add(sample_user)
                db.flush()  # Get the user_id

                # Create sample deck
                sample_deck = Deck(
                    owner_id=sample_user.user_id,
                    title="Sample Deck",
                    description="A sample deck for testing",
                    is_public=True
                )
                db.add(sample_deck)
                db.flush()  # Get the deck_id

                # Create sample cards
                sample_cards = [
                    Card(
                        deck_id=sample_deck.deck_id,
                        front_content="What is the capital of France?",
                        back_content="Paris",
                        position=0
                    ),
                    Card(
                        deck_id=sample_deck.deck_id,
                        front_content="What is 2 + 2?",
                        back_content="4",
                        position=1
                    )
                ]

                for card in sample_cards:
                    db.add(card)

                db.commit()
                logger.info("Sample data seeded successfully")

        except Exception as e:
            logger.error(f"Error seeding sample data: {e}")
            raise


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="ToneCards Lab Database Manager")
    parser.add_argument('action', choices=[
        'create', 'drop', 'recreate', 'list', 'info', 'backup', 'health', 'seed'
    ], help='Action to perform')
    parser.add_argument('--table', help='Table name for info action')
    parser.add_argument('--output', help='Output file for backup action')
    parser.add_argument('--force', action='store_true', help='Force action without confirmation')

    args = parser.parse_args()

    db_manager = DatabaseManager()

    try:
        if args.action == 'create':
            db_manager.create_tables()

        elif args.action == 'drop':
            if not args.force:
                confirm = input("Are you sure you want to drop all tables? (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("Operation cancelled")
                    return
            db_manager.drop_tables()

        elif args.action == 'recreate':
            if not args.force:
                confirm = input("Are you sure you want to recreate all tables? (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("Operation cancelled")
                    return
            db_manager.create_tables(drop_existing=True)

        elif args.action == 'list':
            db_manager.list_tables()

        elif args.action == 'info':
            if not args.table:
                logger.error("--table argument required for info action")
                sys.exit(1)
            info = db_manager.get_table_info(args.table)
            if info:
                print(f"\nTable: {args.table}")
                print(f"Columns: {len(info['columns'])}")
                print(f"Indexes: {len(info['indexes'])}")
                print(f"Foreign Keys: {len(info['foreign_keys'])}")

        elif args.action == 'backup':
            output_file = db_manager.backup_schema(args.output)
            if output_file:
                logger.info(f"Schema backup created: {output_file}")

        elif args.action == 'health':
            healthy = db_manager.check_database_health()
            sys.exit(0 if healthy else 1)

        elif args.action == 'seed':
            db_manager.seed_sample_data()

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

