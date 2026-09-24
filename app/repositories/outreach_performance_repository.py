from typing import List

from app.db.database import get_connection


def get_sent_outreach_performance_rows() -> List[dict]:
    """
    Return one analytics row per SENT outreach message.

    Outcome milestones are converted into boolean flags so
    each outreach remains exactly one row even when it has
    multiple recorded outcomes.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                om.id AS outreach_id,
                om.company_id,
                om.contact_id,
                om.sent_at,

                CASE
                    WHEN oas.id IS NOT NULL
                    THEN 'SNAPSHOT'
                    ELSE 'LEGACY_LIVE'
                END AS attribution_source,

                c.name AS company_name,
                COALESCE(
                    oas.icp_id,
                    c.icp_id
                ) AS icp_id,

                COALESCE(
                    oas.market,
                    c.market
                ) AS market,

                COALESCE(
                    oas.industry,
                    c.industry
                ) AS industry,

                COALESCE(
                    oas.country,
                    c.country
                ) AS country,

                c.employee_count,

                COALESCE(
                    oas.business_model,
                    c.business_model
                ) AS business_model,

                COALESCE(
                    oas.icp_name,
                    i.name
                ) AS icp_name,

                COALESCE(
                    oas.product_id,
                    i.product_id
                ) AS product_id,

                COALESCE(
                    oas.product_name,
                    p.name
                ) AS product_name,

                ct.job_title,

                COALESCE(
                    oas.buyer_category,
                    ct.buyer_category
                ) AS buyer_category,

                MAX(
                    CASE
                        WHEN oo.outcome_type = 'REPLIED'
                        THEN 1
                        ELSE 0
                    END
                ) AS replied,

                MAX(
                    CASE
                        WHEN oo.outcome_type = 'POSITIVE'
                        THEN 1
                        ELSE 0
                    END
                ) AS positive,

                MAX(
                    CASE
                        WHEN oo.outcome_type = 'NEGATIVE'
                        THEN 1
                        ELSE 0
                    END
                ) AS negative,

                MAX(
                    CASE
                        WHEN oo.outcome_type = 'MEETING_BOOKED'
                        THEN 1
                        ELSE 0
                    END
                ) AS meeting_booked

            FROM outreach_messages om

            JOIN companies c
                ON c.id = om.company_id

            JOIN icps i
                ON i.id = c.icp_id

            JOIN products p
                ON p.id = i.product_id

            LEFT JOIN contacts ct
                ON ct.id = om.contact_id

            LEFT JOIN outreach_attribution_snapshots oas
                ON oas.outreach_message_id = om.id

            LEFT JOIN outreach_outcomes oo
                ON oo.outreach_message_id = om.id

            WHERE om.status = 'SENT'

            GROUP BY
                om.id,
                om.company_id,
                om.contact_id,
                om.sent_at,
                CASE
                    WHEN oas.id IS NOT NULL
                    THEN 'SNAPSHOT'
                    ELSE 'LEGACY_LIVE'
                END,
                c.name,
                COALESCE(oas.icp_id, c.icp_id),
                COALESCE(oas.market, c.market),
                COALESCE(oas.industry, c.industry),
                COALESCE(oas.country, c.country),
                c.employee_count,
                COALESCE(oas.business_model, c.business_model),
                COALESCE(oas.icp_name, i.name),
                COALESCE(oas.product_id, i.product_id),
                COALESCE(oas.product_name, p.name),
                ct.job_title,
                COALESCE(oas.buyer_category, ct.buyer_category)

            ORDER BY om.id
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_sent_outreach_signal_rows() -> List[dict]:
    """
    Return one row per unique outreach + signal type.

    New outreach uses the immutable signal snapshot captured
    at send time. Legacy outreach without a snapshot falls
    back to the current company signals.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            WITH snapshot_signals AS (
                SELECT DISTINCT
                    om.id AS outreach_id,
                    json_extract(
                        signal.value,
                        '$.signal_type'
                    ) AS signal_type

                FROM outreach_messages om

                JOIN outreach_attribution_snapshots oas
                    ON oas.outreach_message_id = om.id

                JOIN json_each(
                    oas.signals_json
                ) AS signal

                WHERE om.status = 'SENT'
                  AND json_extract(
                      signal.value,
                      '$.signal_type'
                  ) IS NOT NULL
                  AND TRIM(
                      json_extract(
                          signal.value,
                          '$.signal_type'
                      )
                  ) != ''
            ),

            legacy_signals AS (
                SELECT DISTINCT
                    om.id AS outreach_id,
                    s.signal_type

                FROM outreach_messages om

                JOIN signals s
                    ON s.company_id = om.company_id

                LEFT JOIN outreach_attribution_snapshots oas
                    ON oas.outreach_message_id = om.id

                WHERE om.status = 'SENT'
                  AND oas.id IS NULL
                  AND s.signal_type IS NOT NULL
                  AND TRIM(s.signal_type) != ''
            ),

            attributed_signals AS (
                SELECT
                    outreach_id,
                    signal_type
                FROM snapshot_signals

                UNION

                SELECT
                    outreach_id,
                    signal_type
                FROM legacy_signals
            )

            SELECT
                attributed.outreach_id,
                attributed.signal_type,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id =
                            attributed.outreach_id
                          AND oo.outcome_type = 'REPLIED'
                    )
                    THEN 1
                    ELSE 0
                END AS replied,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id =
                            attributed.outreach_id
                          AND oo.outcome_type = 'POSITIVE'
                    )
                    THEN 1
                    ELSE 0
                END AS positive,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id =
                            attributed.outreach_id
                          AND oo.outcome_type = 'NEGATIVE'
                    )
                    THEN 1
                    ELSE 0
                END AS negative,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id =
                            attributed.outreach_id
                          AND oo.outcome_type = 'MEETING_BOOKED'
                    )
                    THEN 1
                    ELSE 0
                END AS meeting_booked

            FROM attributed_signals attributed

            ORDER BY
                attributed.signal_type,
                attributed.outreach_id
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()
