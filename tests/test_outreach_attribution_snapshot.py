import json

from app.db.database import get_connection
from app.repositories.outreach_attribution_snapshot_repository import (
    create_outreach_attribution_snapshot,
    get_outreach_attribution_snapshot,
)


def _create_snapshot_fixture():
    connection = get_connection()

    try:
        product_id = connection.execute(
            """
            INSERT INTO products (
                name,
                description,
                value_proposition,
                target_problem
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "Snapshot Product",
                "Test product",
                "Test value",
                "Test problem",
            ),
        ).lastrowid

        icp_id = connection.execute(
            """
            INSERT INTO icps (
                product_id,
                name,
                industries,
                company_size_min,
                company_size_max,
                target_market,
                target_countries,
                business_models,
                buyer_categories,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                "Snapshot ICP",
                '["Logistics"]',
                100,
                5000,
                "INDIA",
                '["India"]',
                '["B2B"]',
                '["Operations"]',
                "APPROVED",
            ),
        ).lastrowid

        company_id = connection.execute(
            """
            INSERT INTO companies (
                icp_id,
                name,
                domain,
                country,
                market,
                industry,
                employee_count,
                business_model,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                icp_id,
                "Snapshot Logistics",
                "snapshot-logistics.example",
                "India",
                "INDIA",
                "Logistics",
                1000,
                "B2B",
                "test",
            ),
        ).lastrowid

        contact_id = connection.execute(
            """
            INSERT INTO contacts (
                company_id,
                first_name,
                last_name,
                job_title,
                buyer_category
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                company_id,
                "Test",
                "Buyer",
                "VP Operations",
                "Operations",
            ),
        ).lastrowid

        connection.execute(
            """
            INSERT INTO signals (
                company_id,
                signal_type,
                title,
                description,
                source,
                source_url,
                signal_date,
                confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                "WORKFORCE_TRAINING",
                "Frontline training expansion",
                "Company expanded workforce training.",
                "Company report",
                "https://example.com/report",
                "2026-09-01",
                0.9,
            ),
        )

        outreach_id = connection.execute(
            """
            INSERT INTO outreach_messages (
                company_id,
                contact_id,
                subject,
                message_body,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                company_id,
                contact_id,
                "Snapshot test",
                "Test outreach message.",
                "APPROVED",
            ),
        ).lastrowid

        connection.commit()

        return {
            "product_id": product_id,
            "icp_id": icp_id,
            "company_id": company_id,
            "contact_id": contact_id,
            "outreach_id": outreach_id,
        }

    finally:
        connection.close()


def test_snapshot_captures_attribution_context():
    fixture = _create_snapshot_fixture()

    snapshot = create_outreach_attribution_snapshot(
        fixture["outreach_id"]
    )

    assert snapshot["outreach_message_id"] == fixture["outreach_id"]
    assert snapshot["product_id"] == fixture["product_id"]
    assert snapshot["product_name"] == "Snapshot Product"
    assert snapshot["icp_id"] == fixture["icp_id"]
    assert snapshot["icp_name"] == "Snapshot ICP"
    assert snapshot["market"] == "INDIA"
    assert snapshot["country"] == "India"
    assert snapshot["industry"] == "Logistics"
    assert snapshot["business_model"] == "B2B"
    assert snapshot["buyer_category"] == "Operations"

    assert len(snapshot["signals"]) == 1
    assert snapshot["signals"][0]["signal_type"] == "WORKFORCE_TRAINING"
    assert snapshot["signals"][0]["title"] == "Frontline training expansion"


def test_snapshot_remains_immutable_after_source_changes():
    fixture = _create_snapshot_fixture()

    first = create_outreach_attribution_snapshot(
        fixture["outreach_id"]
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE companies
            SET market = ?,
                country = ?,
                industry = ?,
                business_model = ?
            WHERE id = ?
            """,
            (
                "INTERNATIONAL",
                "United Kingdom",
                "Software",
                "B2B SaaS",
                fixture["company_id"],
            ),
        )

        connection.execute(
            """
            UPDATE contacts
            SET buyer_category = ?
            WHERE id = ?
            """,
            (
                "Learning & Development",
                fixture["contact_id"],
            ),
        )

        connection.execute(
            """
            INSERT INTO signals (
                company_id,
                signal_type,
                title,
                confidence
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                fixture["company_id"],
                "HIRING",
                "New hiring signal",
                0.8,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    second = create_outreach_attribution_snapshot(
        fixture["outreach_id"]
    )

    assert second["id"] == first["id"]
    assert second["market"] == "INDIA"
    assert second["country"] == "India"
    assert second["industry"] == "Logistics"
    assert second["business_model"] == "B2B"
    assert second["buyer_category"] == "Operations"

    assert len(second["signals"]) == 1
    assert second["signals"][0]["signal_type"] == "WORKFORCE_TRAINING"


def test_get_snapshot_returns_saved_signal_json():
    fixture = _create_snapshot_fixture()

    created = create_outreach_attribution_snapshot(
        fixture["outreach_id"]
    )

    fetched = get_outreach_attribution_snapshot(
        fixture["outreach_id"]
    )

    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["signals"] == created["signals"]

    raw_signals = json.loads(
        fetched["signals_json"]
    )

    assert raw_signals == fetched["signals"]
