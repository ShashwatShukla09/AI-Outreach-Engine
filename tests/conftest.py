import os
from pathlib import Path


TEST_DATABASE_PATH = (
    Path(__file__).resolve().parent
    / ".pytest_buyer_intelligence.db"
)

# This runs while pytest is loading conftest.py,
# before test modules import the application database.
os.environ["BUYER_INTELLIGENCE_DATABASE_PATH"] = str(
    TEST_DATABASE_PATH
)


def pytest_sessionstart(session):
    """
    Create a clean isolated database for the pytest session.
    """

    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink()

    from app.db.schema import create_tables

    create_tables()


def pytest_sessionfinish(session, exitstatus):
    """
    Remove the isolated pytest database after the test run.
    """

    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink()
