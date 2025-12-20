#!/usr/bin/env python3
"""Quick database setup script for development with MySQL and PostgreSQL support."""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tcl_api.repository.db.database import setup_database, drop_db, get_db_context, DB_TYPE
from tcl_api.repository.db.models import User, Deck, Card, RendererType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def quick_setup():
    """Quick database setup with sample data."""
    try:
        logger.info(f"Setting up {DB_TYPE} database for development...")

        # Create database and all tables
        setup_database()
        logger.info("Database setup completed")

        # Add sample data
        with get_db_context() as db:
            # Check if data already exists
            if db.query(User).count() > 0:
                logger.info("Database already has data, skipping sample data creation")
                return

            # Create sample user
            user = User(
                email="dev@tonecards.com",
                name="Development User",
                preferences={
                    "theme": "dark",
                    "language": "en",
                    "notifications": True
                }
            )
            db.add(user)
            db.flush()

            # Create sample decks
            decks = [
                Deck(
                    owner_id=user.user_id,
                    title="Music Theory Basics",
                    description="Essential music theory concepts",
                    is_public=True
                ),
                Deck(
                    owner_id=user.user_id,
                    title="Guitar Chords",
                    description="Common guitar chord progressions",
                    is_public=False
                ),
                Deck(
                    owner_id=user.user_id,
                    title="Piano Scales",
                    description="Major and minor scales for piano",
                    is_public=True
                )
            ]

            for deck in decks:
                db.add(deck)
            db.flush()

            # Create sample cards for Music Theory deck
            music_theory_cards = [
                Card(
                    deck_id=decks[0].deck_id,
                    front_content="What is a major scale?",
                    back_content="A major scale is a seven-note musical scale with the pattern: W-W-H-W-W-W-H (where W = whole step, H = half step)",
                    front_renderer=RendererType.STRING,
                    back_renderer=RendererType.MARKDOWN,
                    position=0
                ),
                Card(
                    deck_id=decks[0].deck_id,
                    front_content="What are the notes in C major scale?",
                    back_content="C - D - E - F - G - A - B - C",
                    position=1
                ),
                Card(
                    deck_id=decks[0].deck_id,
                    front_content="What is a perfect fifth?",
                    back_content="A perfect fifth is an interval of 7 semitones (e.g., C to G)",
                    position=2
                )
            ]

            # Create sample cards for Guitar Chords deck
            guitar_cards = [
                Card(
                    deck_id=decks[1].deck_id,
                    front_content="Show the C major chord fingering",
                    back_content="```\nE|---0---\nB|---1---\nG|---0---\nD|---2---\nA|---3---\nE|-------\n```",
                    front_renderer=RendererType.STRING,
                    back_renderer=RendererType.MARKDOWN,
                    position=0
                ),
                Card(
                    deck_id=decks[1].deck_id,
                    front_content="What is the I-V-vi-IV progression in C major?",
                    back_content="C - G - Am - F",
                    position=1
                )
            ]

            # Create sample cards for Piano Scales deck with ABC notation
            piano_cards = [
                Card(
                    deck_id=decks[2].deck_id,
                    front_content="C Major Scale",
                    back_content="X:1\nT:C Major Scale\nM:4/4\nL:1/4\nK:C\nC D E F | G A B c |]",
                    front_renderer=RendererType.STRING,
                    back_renderer=RendererType.ABC_JS,
                    position=0
                ),
                Card(
                    deck_id=decks[2].deck_id,
                    front_content="A Minor Scale (Natural)",
                    back_content="X:1\nT:A Minor Scale\nM:4/4\nL:1/4\nK:Am\nA B c d | e f g a |]",
                    front_renderer=RendererType.STRING,
                    back_renderer=RendererType.ABC_JS,
                    position=1
                )
            ]

            all_cards = music_theory_cards + guitar_cards + piano_cards
            for card in all_cards:
                db.add(card)

            db.commit()

            logger.info(f"Created sample data:")
            logger.info(f"  - 1 user: {user.email}")
            logger.info(f"  - {len(decks)} decks")
            logger.info(f"  - {len(all_cards)} cards")

        logger.info(f"Development {DB_TYPE} database setup completed!")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    try:
        logger.warning(f"Resetting {DB_TYPE} database - all data will be lost!")

        # Drop all tables
        drop_db()
        logger.info("Database tables dropped")

        # Recreate with sample data
        quick_setup()

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        confirm = input("Are you sure you want to reset the database? All data will be lost! (yes/no): ")
        if confirm.lower() == "yes":
            reset_database()
        else:
            logger.info("Database reset cancelled")
    else:
        quick_setup()


if __name__ == "__main__":
    main()

