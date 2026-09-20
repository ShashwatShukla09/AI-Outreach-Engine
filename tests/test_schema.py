from app.db.database import get_connection
from app.db.schema import create_tables


def get_table_names():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        return {row["name"] for row in rows}

    finally:
        connection.close()


def get_foreign_key_tables(table_name):
    connection = get_connection()

    try:
        rows = connection.execute(
            f"PRAGMA foreign_key_list({table_name})"
        ).fetchall()

        return {row["table"] for row in rows}

    finally:
        connection.close()


def test_all_v1_tables_exist():
    create_tables()

    table_names = get_table_names()

    expected_tables = {
        "products",
        "icps",
        "companies",
        "company_scores",
        "signals",
        "account_research",
        "contacts",
        "enrichment_jobs",
        "outreach_messages",
        "outreach_events",
    }

    assert expected_tables.issubset(table_names)


def test_foreign_keys_enabled():
    connection = get_connection()

    try:
        result = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()

        assert result[0] == 1

    finally:
        connection.close()


def test_company_score_relationship():
    assert "companies" in get_foreign_key_tables("company_scores")


def test_contacts_relationship():
    assert "companies" in get_foreign_key_tables("contacts")


def test_enrichment_relationship():
    assert "companies" in get_foreign_key_tables("enrichment_jobs")


def test_outreach_relationships():
    references = get_foreign_key_tables("outreach_messages")

    assert "companies" in references
    assert "contacts" in references


def test_outreach_event_relationship():
    assert "outreach_messages" in get_foreign_key_tables(
        "outreach_events"
    )
