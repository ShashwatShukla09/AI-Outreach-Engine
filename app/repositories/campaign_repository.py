from typing import List, Optional

from app.db.database import get_connection


def create_campaign(
    product_id: int,
    icp_id: int,
    name: str,
    market: Optional[str] = None,
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO campaigns (
                product_id,
                icp_id,
                name,
                market,
                status
            )
            VALUES (?, ?, ?, ?, 'DRAFT')
            """,
            (
                product_id,
                icp_id,
                name,
                market,
            ),
        )

        campaign_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_campaign(
    campaign_id: int,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def list_campaigns() -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM campaigns
            ORDER BY id DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def update_campaign_status(
    campaign_id: int,
    status: str,
) -> Optional[dict]:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE campaigns
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                campaign_id,
            ),
        )

        connection.commit()

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            """
            SELECT *
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def add_company_to_campaign(
    campaign_id: int,
    company_id: int,
) -> None:
    connection = get_connection()

    try:
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

    finally:
        connection.close()


def remove_company_from_campaign(
    campaign_id: int,
    company_id: int,
) -> bool:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM campaign_companies
            WHERE campaign_id = ?
              AND company_id = ?
            """,
            (
                campaign_id,
                company_id,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_campaign_companies(
    campaign_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                c.*,
                cc.added_at AS campaign_added_at
            FROM campaign_companies cc
            JOIN companies c
                ON c.id = cc.company_id
            WHERE cc.campaign_id = ?
            ORDER BY cc.added_at DESC,
                     c.id DESC
            """,
            (campaign_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()
