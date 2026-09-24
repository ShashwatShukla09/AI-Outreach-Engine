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

                c.name AS company_name,
                c.industry,
                c.country,
                c.employee_count,
                c.business_model,

                ct.job_title,
                ct.buyer_category,

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

            LEFT JOIN contacts ct
                ON ct.id = om.contact_id

            LEFT JOIN outreach_outcomes oo
                ON oo.outreach_message_id = om.id

            WHERE om.status = 'SENT'

            GROUP BY
                om.id,
                om.company_id,
                om.contact_id,
                om.sent_at,
                c.name,
                c.industry,
                c.country,
                c.employee_count,
                c.business_model,
                ct.job_title,
                ct.buyer_category

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

    A company may have multiple individual signals of the same
    type. DISTINCT prevents those duplicate signal records from
    counting the same outreach more than once inside that cohort.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT DISTINCT
                om.id AS outreach_id,
                s.signal_type,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id = om.id
                          AND oo.outcome_type = 'REPLIED'
                    )
                    THEN 1
                    ELSE 0
                END AS replied,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id = om.id
                          AND oo.outcome_type = 'POSITIVE'
                    )
                    THEN 1
                    ELSE 0
                END AS positive,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id = om.id
                          AND oo.outcome_type = 'NEGATIVE'
                    )
                    THEN 1
                    ELSE 0
                END AS negative,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM outreach_outcomes oo
                        WHERE oo.outreach_message_id = om.id
                          AND oo.outcome_type = 'MEETING_BOOKED'
                    )
                    THEN 1
                    ELSE 0
                END AS meeting_booked

            FROM outreach_messages om

            JOIN signals s
                ON s.company_id = om.company_id

            WHERE om.status = 'SENT'
              AND s.signal_type IS NOT NULL
              AND TRIM(s.signal_type) != ''

            ORDER BY
                s.signal_type,
                om.id
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()
