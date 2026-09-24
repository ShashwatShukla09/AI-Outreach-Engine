from app.db.database import get_connection
from app.repositories.outreach_performance_repository import (
    get_sent_outreach_performance_rows,
    get_sent_outreach_signal_rows,
)
from app.services.outreach_outcome_service import (
    record_outreach_outcome,
)
from app.services.outreach_performance_service import (
    _calculate_attribution_summary,
    get_outreach_performance,
)
from app.services.outreach_execution_service import (
    execute_outreach,
)
from app.services.outreach_review_service import (
    approve_outreach_message,
)
from app.providers.execution.mock_provider import (
    MockExecutionProvider,
)
from tests.test_outreach_execution import (
    prepare_draft,
)


def _set_company_segment(
    company_id: int,
    industry: str,
    business_model: str,
) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE companies
            SET industry = ?,
                business_model = ?
            WHERE id = ?
            """,
            (
                industry,
                business_model,
                company_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def _set_buyer_category(
    contact_id: int,
    buyer_category: str,
) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE contacts
            SET buyer_category = ?
            WHERE id = ?
            """,
            (
                buyer_category,
                contact_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def _create_sent_outreach(
    industry: str,
    buyer_category: str,
    business_model: str,
    before_send=None,
) -> dict:
    draft = prepare_draft()

    _set_company_segment(
        draft["company_id"],
        industry,
        business_model,
    )

    _set_buyer_category(
        draft["contact_id"],
        buyer_category,
    )

    approve_outreach_message(
        draft["id"]
    )

    if before_send is not None:
        before_send(draft)

    execute_outreach(
        outreach_id=draft["id"],
        provider=MockExecutionProvider(),
    )

    return {
        "id": draft["id"],
        "company_id": draft["company_id"],
        "contact_id": draft["contact_id"],
    }


def _find_segment(
    segments,
    name: str,
) -> dict:
    return next(
        segment
        for segment in segments
        if segment["segment"] == name
    )


def test_performance_counts_outreach_once():
    baseline = get_outreach_performance()["overall"]

    outreach = _create_sent_outreach(
        industry="Test Logistics",
        buyer_category="Operations",
        business_model="B2B",
    )

    record_outreach_outcome(
        outreach["id"],
        "REPLIED",
    )
    record_outreach_outcome(
        outreach["id"],
        "POSITIVE",
    )
    record_outreach_outcome(
        outreach["id"],
        "MEETING_BOOKED",
    )

    metrics = get_outreach_performance()["overall"]

    assert metrics["sent"] == baseline["sent"] + 1
    assert metrics["replied"] == baseline["replied"] + 1
    assert metrics["positive"] == baseline["positive"] + 1
    assert (
        metrics["meetings_booked"]
        == baseline["meetings_booked"] + 1
    )


def test_performance_groups_by_company_and_buyer():
    outreach = _create_sent_outreach(
        industry="Test Manufacturing",
        buyer_category="Learning & Development",
        business_model="Enterprise",
    )

    record_outreach_outcome(
        outreach["id"],
        "REPLIED",
    )

    performance = get_outreach_performance()

    industry = _find_segment(
        performance["by_industry"],
        "Test Manufacturing",
    )

    buyer = _find_segment(
        performance["by_buyer_category"],
        "Learning & Development",
    )

    model = _find_segment(
        performance["by_business_model"],
        "Enterprise",
    )

    assert industry["sent"] >= 1
    assert industry["replied"] >= 1

    assert buyer["sent"] >= 1
    assert buyer["replied"] >= 1

    assert model["sent"] >= 1
    assert model["replied"] >= 1


def test_small_sample_is_insufficient_data():
    from app.services.outreach_performance_service import (
        _evidence_status,
    )

    assert _evidence_status(1) == "INSUFFICIENT_DATA"
    assert _evidence_status(2) == "INSUFFICIENT_DATA"
    assert _evidence_status(4) == "INSUFFICIENT_DATA"


def test_five_sent_messages_become_early_signal():
    segment_name = "Five Message Test Segment"

    for index in range(5):
        outreach = _create_sent_outreach(
            industry=segment_name,
            buyer_category="Test Buyer",
            business_model="Test Model",
        )

        if index == 0:
            record_outreach_outcome(
                outreach["id"],
                "REPLIED",
            )

    performance = get_outreach_performance()

    segment = _find_segment(
        performance["by_industry"],
        segment_name,
    )

    assert segment["sent"] == 5
    assert segment["replied"] == 1
    assert segment["reply_rate"] == 20.0
    assert segment["evidence_status"] == "EARLY_SIGNAL"


def test_signal_performance_does_not_double_count_same_type():
    def add_signals_before_send(draft):
        connection = get_connection()

        try:
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
                    draft["company_id"],
                    "TEST_EXPANSION",
                    "First expansion signal",
                    "HIGH",
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
                    draft["company_id"],
                    "TEST_EXPANSION",
                    "Second expansion signal",
                    "HIGH",
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
                    draft["company_id"],
                    "TEST_HIRING",
                    "Hiring signal",
                    "HIGH",
                ),
            )

            connection.commit()

        finally:
            connection.close()

    outreach = _create_sent_outreach(
        industry="Signal Test Industry",
        buyer_category="Signal Test Buyer",
        business_model="Signal Test Model",
        before_send=add_signals_before_send,
    )

    record_outreach_outcome(
        outreach["id"],
        "REPLIED",
    )

    performance = get_outreach_performance()

    expansion = _find_segment(
        performance["by_signal_type"],
        "TEST_EXPANSION",
    )

    hiring = _find_segment(
        performance["by_signal_type"],
        "TEST_HIRING",
    )

    assert expansion["sent"] == 1
    assert expansion["replied"] == 1
    assert expansion["reply_rate"] == 100.0

    assert hiring["sent"] == 1
    assert hiring["replied"] == 1
    assert hiring["reply_rate"] == 100.0


def test_performance_segments_by_product_icp_market_and_country():
    first = _create_sent_outreach(
        industry="Test SaaS",
        buyer_category="Operations",
        business_model="B2B SaaS",
    )

    second = _create_sent_outreach(
        industry="Test SaaS",
        buyer_category="Operations",
        business_model="B2B SaaS",
    )

    performance = get_outreach_performance()

    expected_keys = {
        "by_product",
        "by_icp",
        "by_market",
        "by_country",
    }

    assert expected_keys.issubset(performance.keys())

    for key in expected_keys:
        total_sent = sum(
            segment["sent"]
            for segment in performance[key]
        )

        assert total_sent == performance["overall"]["sent"]

    assert performance["overall"]["sent"] >= 2

    created_ids = {
        first["id"],
        second["id"],
    }

    assert len(created_ids) == 2


def test_non_sent_outreach_does_not_enter_performance_segments():
    performance = get_outreach_performance()

    overall_sent = performance["overall"]["sent"]

    for key in [
        "by_product",
        "by_icp",
        "by_market",
        "by_country",
    ]:
        segmented_sent = sum(
            segment["sent"]
            for segment in performance[key]
        )

        assert segmented_sent == overall_sent


def test_sent_performance_uses_frozen_attribution_snapshot():
    sent = _create_sent_outreach(
        industry="Logistics",
        buyer_category="Operations",
        business_model="B2B",
    )

    before = get_outreach_performance()

    original_row = next(
        row
        for row in get_sent_outreach_performance_rows()
        if row["outreach_id"] == sent["id"]
    )

    original_product = original_row["product_name"]
    original_icp = original_row["icp_name"]
    original_market = original_row["market"]
    original_country = original_row["country"]
    original_industry = original_row["industry"]
    original_business_model = original_row["business_model"]
    original_buyer_category = original_row["buyer_category"]

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
                "CHANGED_MARKET",
                "Changed Country",
                "Changed Industry",
                "Changed Model",
                sent["company_id"],
            ),
        )

        connection.execute(
            """
            UPDATE contacts
            SET buyer_category = ?
            WHERE id = ?
            """,
            (
                "Changed Buyer",
                sent["contact_id"],
            ),
        )

        connection.commit()

    finally:
        connection.close()

    after_row = next(
        row
        for row in get_sent_outreach_performance_rows()
        if row["outreach_id"] == sent["id"]
    )

    assert after_row["product_name"] == original_product
    assert after_row["icp_name"] == original_icp
    assert after_row["market"] == original_market
    assert after_row["country"] == original_country
    assert after_row["industry"] == original_industry
    assert after_row["business_model"] == original_business_model
    assert after_row["buyer_category"] == original_buyer_category

    after = get_outreach_performance()

    assert (
        sum(item["sent"] for item in before["by_market"])
        ==
        sum(item["sent"] for item in after["by_market"])
    )


def test_signal_added_after_send_is_not_attributed_to_old_outreach():
    outreach = _create_sent_outreach(
        industry="Post Send Signal Industry",
        buyer_category="Operations",
        business_model="B2B",
    )

    rows_before = get_sent_outreach_signal_rows()

    before_types = {
        row["signal_type"]
        for row in rows_before
        if row["outreach_id"] == outreach["id"]
    }

    connection = get_connection()

    try:
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
                outreach["company_id"],
                "POST_SEND_SIGNAL",
                "Signal discovered after outreach",
                "HIGH",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    rows_after = get_sent_outreach_signal_rows()

    after_types = {
        row["signal_type"]
        for row in rows_after
        if row["outreach_id"] == outreach["id"]
    }

    assert "POST_SEND_SIGNAL" not in before_types
    assert "POST_SEND_SIGNAL" not in after_types
    assert after_types == before_types


def test_sent_performance_exposes_snapshot_attribution_source():
    outreach = _create_sent_outreach(
        industry="Attribution Test Industry",
        buyer_category="Operations",
        business_model="B2B",
    )

    row = next(
        item
        for item in get_sent_outreach_performance_rows()
        if item["outreach_id"] == outreach["id"]
    )

    assert row["attribution_source"] == "SNAPSHOT"


def test_sent_performance_exposes_legacy_live_attribution_source():
    outreach = _create_sent_outreach(
        industry="Legacy Attribution Industry",
        buyer_category="Operations",
        business_model="B2B",
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM outreach_attribution_snapshots
            WHERE outreach_message_id = ?
            """,
            (
                outreach["id"],
            ),
        )

        connection.commit()

    finally:
        connection.close()

    row = next(
        item
        for item in get_sent_outreach_performance_rows()
        if item["outreach_id"] == outreach["id"]
    )

    assert row["attribution_source"] == "LEGACY_LIVE"


def test_performance_reports_attribution_coverage():
    snapshot_outreach = _create_sent_outreach(
        industry="Coverage Snapshot Industry",
        buyer_category="Operations",
        business_model="B2B",
    )

    legacy_outreach = _create_sent_outreach(
        industry="Coverage Legacy Industry",
        buyer_category="Operations",
        business_model="B2B",
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM outreach_attribution_snapshots
            WHERE outreach_message_id = ?
            """,
            (
                legacy_outreach["id"],
            ),
        )

        connection.commit()

    finally:
        connection.close()

    performance = get_outreach_performance()
    attribution = performance["attribution"]

    rows = get_sent_outreach_performance_rows()

    expected_snapshot_count = sum(
        1
        for row in rows
        if row["attribution_source"] == "SNAPSHOT"
    )

    expected_legacy_count = sum(
        1
        for row in rows
        if row["attribution_source"] == "LEGACY_LIVE"
    )

    assert snapshot_outreach["id"] != legacy_outreach["id"]

    assert attribution["total_sent"] == len(rows)
    assert attribution["snapshot_count"] == expected_snapshot_count
    assert attribution["legacy_live_count"] == expected_legacy_count

    assert (
        attribution["snapshot_count"]
        + attribution["legacy_live_count"]
        == attribution["total_sent"]
    )

    assert attribution["snapshot_coverage"] == round(
        expected_snapshot_count / len(rows) * 100,
        1,
    )


def test_attribution_summary_handles_zero_sent():
    attribution = _calculate_attribution_summary([])

    assert attribution == {
        "total_sent": 0,
        "snapshot_count": 0,
        "legacy_live_count": 0,
        "snapshot_coverage": 0.0,
    }
