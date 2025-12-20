#!/bin/bash
# Database Setup Scripts for ToneCards Lab API
# Usage: Run this script from the project root directory

echo "ToneCards Lab Database Setup"
echo "==========================="

# Create database and tables
echo
echo "1. Creating database and tables..."
python3 scripts/db/create_database.py

# Check database health
echo
echo "2. Checking database health..."
python3 scripts/db/manage_database.py health

# Set up development data
echo
echo "3. Setting up development data..."
python3 scripts/db/dev_setup.py

echo
echo "Database setup completed!"
echo
echo "Available management commands:"
echo "  python3 scripts/db/manage_database.py list              - List all tables"
echo "  python3 scripts/db/manage_database.py health            - Check database health"
echo "  python3 scripts/db/manage_database.py seed              - Add sample data"
echo "  python3 scripts/db/manage_database.py backup            - Backup schema"
echo "  python3 scripts/db/dev_setup.py reset                   - Reset with sample data"
echo
echo "For migrations (requires Alembic):"
echo "  python3 scripts/db/migrate.py init                      - Initialize Alembic"
echo "  python3 scripts/db/migrate.py upgrade                   - Run migrations"
echo "  python3 scripts/db/migrate.py revision 'message'        - Create new migration"

