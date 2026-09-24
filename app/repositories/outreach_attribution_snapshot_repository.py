import json
from typing import Optional

from app.db.database import get_connection


def get_outreach_attribution_snapshot(
    outreach_message_id: int,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM outreach_attribution_snapshots
            WHERE outreach_message_id = ?
            """,
            (outreach_message_id,),
        ).fetchone()

        if row is None:
            return None

        snapshot = dict(row)

        try:
            snapshot["signals"] = json.loads(
                snapshot["signals_json"]
            )
        except (TypeError, json.JSONDecodeError):
            snapshot["signals"] = []

        return snapshot

    finally:
        connection.close()


def create_outreach_attribution_snapshot(
    outreach_message_id: int,
) -> dict:
    existing = get_outreach_attribution_snapshot(
        outreach_message_id
    )

    if existing is not None:
        return existing

    connection = get_connection()

    try:
        context = connection.execute(
            """
            SELECT
                om.id AS outreach_message_id,

                c.id AS company_id,
                c.market,
                c.country,
                c.industry,
                c.business_model,

                ct.buyer_category,

                i.id AS icp_id,
                i.name AS icp_name,

                p.id AS product_id,
                p.name AS product_name

            FROM outreach_messages om

            JOIN companies c
                ON c.id = om.company_id

            JOIN icps i
                ON i.id = c.icp_id

            JOIN products p
                ON p.id = i.product_id

            LEFT JOIN contacts ct
                ON ct.id = om.contact_id

            WHERE om.id = ?
            """,
            (outreach_message_id,),
        ).fetchone()

        if context is None:
            raise ValueError(
                "Outreach attribution context not found."
            )

        signal_rows = connection.execute(
            """
            SELECT
                id,
                signal_type,
                title,
                description,
                source,
                source_url,
                signal_date,
                confidence,
                created_at
            FROM signals
            WHERE company_id = ?
            ORDER BY id
            """,
            (context["company_id"],),
        ).fetchall()

        signals = [
            dict(row)
            for row in signal_rows
        ]

        signals_json = json.dumps(
            signals,
            ensure_ascii=False,
            sort_keys=True,
        )

        try:
            cursor = connection.execute(
                """
                INSERT INTO outreach_attribution_snapshots (
                    outreach_message_id,
                    product_id,
                    product_name,
                    icp_id,
                    icp_name,
                    market,
                    country,
                    industry,
                    business_model,
                    buyer_category,
                    signals_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    context["outreach_message_id"],
                    context["product_id"],
                    context["product_name"],
                    context["icp_id"],
                    context["icp_name"],
                    context["market"],
                    context["country"],
                    context["industry"],
                    context["business_model"],
                    context["buyer_category"],
                    signals_json,
                ),
            )

            snapshot_id = cursor.lastrowid
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        row = connection.execute(
            """
            SELECT *
            FROM outreach_attribution_snapshots
            WHERE id = ?
            """,
            (snapshot_id,),
        ).fetchone()

        snapshot = dict(row)
        snapshot["signals"] = json.loads(
            snapshot["signals_json"]
        )

        return snapshot

    finally:
        connection.close()
