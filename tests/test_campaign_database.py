import sqlite3

import pytest

from app.db.database import get_connection


def _create_campaign_foundation():
    connection = get_connection()

    try:
        product_cursor = connection.execute(
            """
            INSERT INTO products (
                name,
                description
            )
            VALUES (?, ?)
            """,
            (
                "Campaign Test Product",
                "Campaign database test product",
            ),
        )
        product_id = product_cursor.lastrowid

        icp_cursor = connection.execute(
            """
            INSERT INTO icps (
                product_id,
                name,
                target_market,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                product_id,
                "Campaign Test ICP",
                "India",
                "APPROVED",
            ),
        )
        icp_id = icp_cursor.lastrowid

        company_cursor = connection.execute(
            """
            INSERT INTO companies (
                icp_id,
                name,
                domain
            )
            VALUES (?, ?, ?)
            """,
            (
                icp_id,
                "Campaign Test Company",
                "campaign-test.example",
            ),
        )
        company_id = company_cursor.lastrowid

        connection.commit()

        return product_id, icp_id, company_id

    finally:
        connection.close()


def test_campaign_tables_exist():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'campaigns',
                  'campaign_companies'
              )
            ORDER BY name
            """
        ).fetchall()

        assert [
            row["name"]
            for row in rows
        ] == [
            "campaign_companies",
            "campaigns",
        ]

    finally:
        connection.close()


def test_campaign_can_contain_company():
    product_id, icp_id, company_id = (
        _create_campaign_foundation()
    )

    connection = get_connection()

    try:
        campaign_cursor = connection.execute(
            """
            INSERT INTO campaigns (
                product_id,
                icp_id,
                name,
                market,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                product_id,
                icp_id,
                "India Operations",
                "India",
                "ACTIVE",
            ),
        )
        campaign_id = campaign_cursor.lastrowid

        connection.execute(
            """
            INSERT INTO campaign_companies (
                campaign_id,
                company_id
            )
            VALUES (?, ?)
            """,
            (
                campaign_id,
                company_id,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT
                ca.name AS campaign_name,
                ca.status,
                c.name AS company_name
            FROM campaigns ca
            JOIN campaign_companies cc
                ON cc.campaign_id = ca.id
            JOIN companies c
                ON c.id = cc.company_id
            WHERE ca.id = ?
            """,
            (campaign_id,),
        ).fetchone()

        assert row["campaign_name"] == "India Operations"
        assert row["status"] == "ACTIVE"
        assert row["company_name"] == "Campaign Test Company"

    finally:
        connection.close()


def test_company_cannot_be_added_twice_to_same_campaign():
    product_id, icp_id, company_id = (
        _create_campaign_foundation()
    )

    connection = get_connection()

    try:
        campaign_cursor = connection.execute(
            """
            INSERT INTO campaigns (
                product_id,
                icp_id,
                name,
                market
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                product_id,
                icp_id,
                "Duplicate Membership Test",
                "India",
            ),
        )
        campaign_id = campaign_cursor.lastrowid

        connection.execute(
            """
            INSERT INTO campaign_companies (
                campaign_id,
                company_id
            )
            VALUES (?, ?)
            """,
            (
                campaign_id,
                company_id,
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO campaign_companies (
                    campaign_id,
                    company_id
                )
                VALUES (?, ?)
                """,
                (
                    campaign_id,
                    company_id,
                ),
            )

    finally:
        connection.rollback()
        connection.close()


def test_campaign_rejects_invalid_status():
    product_id, icp_id, _ = (
        _create_campaign_foundation()
    )

    connection = get_connection()

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO campaigns (
                    product_id,
                    icp_id,
                    name,
                    market,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    icp_id,
                    "Invalid Status Test",
                    "India",
                    "INVALID",
                ),
            )

    finally:
        connection.rollback()
        connection.close()
