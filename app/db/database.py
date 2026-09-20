import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "buyer_intelligence.db"


def get_connection() -> sqlite3.Connection:
    """
    Create and return a connection to the local SQLite database.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    # This allows us to access database columns by name later.
    connection.row_factory = sqlite3.Row

    # SQLite does not enforce foreign keys by default.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def check_database() -> bool:
    """
    Test whether the application can communicate with SQLite.
    """

    connection = get_connection()

    try:
        connection.execute("SELECT 1")
        return True
    finally:
        connection.close()
