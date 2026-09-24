from app.services.outreach_learning_service import (
    _build_learning,
    get_outreach_learnings,
)
from tests.test_outreach_performance import (
    _create_sent_outreach,
)


def test_insufficient_data_does_not_claim_performance():
    metrics = {
        "segment": "Operations",
        "sent": 2,
        "replied": 1,
        "positive": 1,
        "negative": 0,
        "meetings_booked": 0,
        "reply_rate": 50.0,
        "positive_reply_rate": 50.0,
        "negative_reply_rate": 0.0,
        "meeting_rate": 0.0,
        "evidence_status": "INSUFFICIENT_DATA",
    }

    learning = _build_learning(
        dimension="buyer category",
        metrics=metrics,
    )

    assert learning["status"] == "INSUFFICIENT_DATA"
    assert "only 2 sent outreach samples" in learning["message"]
    assert "More data is needed" in learning["message"]

    # A tiny sample must not be presented as a performance insight.
    assert "50.0% reply rate" not in learning["message"]


def test_early_signal_reports_observed_metrics():
    metrics = {
        "segment": "Operations",
        "sent": 10,
        "replied": 3,
        "positive": 2,
        "negative": 1,
        "meetings_booked": 1,
        "reply_rate": 30.0,
        "positive_reply_rate": 20.0,
        "negative_reply_rate": 10.0,
        "meeting_rate": 10.0,
        "evidence_status": "EARLY_SIGNAL",
    }

    learning = _build_learning(
        dimension="buyer category",
        metrics=metrics,
    )

    assert learning["status"] == "EARLY_SIGNAL"
    assert "30.0% reply rate" in learning["message"]
    assert "20.0% positive reply rate" in learning["message"]
    assert "10.0% meeting rate" in learning["message"]
    assert "across 10 sent outreach messages" in learning["message"]


def test_learning_service_includes_all_dimensions():
    outreach = _create_sent_outreach(
        industry="Learning Test Industry",
        buyer_category="Learning Test Buyer",
        business_model="Learning Test Model",
    )

    from app.db.database import get_connection

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
                "LEARNING_TEST_SIGNAL",
                "Learning test signal",
                "HIGH",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    learnings = get_outreach_learnings()

    dimensions = {
        learning["dimension"]
        for learning in learnings
    }

    assert "industry" in dimensions
    assert "buyer category" in dimensions
    assert "business model" in dimensions
    assert "signal type" in dimensions
    assert "product" in dimensions
    assert "ICP" in dimensions
    assert "market" in dimensions
    assert "country" in dimensions


def test_learning_contains_metrics_and_segment():
    learnings = get_outreach_learnings()

    for learning in learnings:
        assert learning["segment"]
        assert learning["message"]
        assert "metrics" in learning
        assert "sent" in learning["metrics"]
        assert "reply_rate" in learning["metrics"]
        assert "meeting_rate" in learning["metrics"]
