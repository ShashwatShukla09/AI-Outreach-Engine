from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_outreach_performance_endpoint():
    response = client.get(
        "/api/outreach/performance"
    )

    assert response.status_code == 200

    data = response.json()

    assert "overall" in data
    assert "by_industry" in data
    assert "by_buyer_category" in data
    assert "by_business_model" in data
    assert "by_signal_type" in data
    assert "by_product" in data
    assert "by_icp" in data
    assert "by_market" in data
    assert "by_country" in data
    assert "learnings" in data

    overall = data["overall"]

    assert "sent" in overall
    assert "replied" in overall
    assert "positive" in overall
    assert "negative" in overall
    assert "meetings_booked" in overall

    assert "reply_rate" in overall
    assert "positive_reply_rate" in overall
    assert "negative_reply_rate" in overall
    assert "meeting_rate" in overall

    assert overall["evidence_status"] in {
        "NO_DATA",
        "INSUFFICIENT_DATA",
        "EARLY_SIGNAL",
    }


def test_outreach_performance_segments_have_metrics():
    response = client.get(
        "/api/outreach/performance"
    )

    assert response.status_code == 200

    data = response.json()

    segment_groups = (
        "by_industry",
        "by_buyer_category",
        "by_business_model",
        "by_product",
        "by_icp",
        "by_market",
        "by_country",
    )

    for group_name in segment_groups:
        for segment in data[group_name]:
            assert "segment" in segment
            assert "sent" in segment
            assert "replied" in segment
            assert "positive" in segment
            assert "negative" in segment
            assert "meetings_booked" in segment
            assert "reply_rate" in segment
            assert "meeting_rate" in segment
            assert segment["evidence_status"] in {
                "INSUFFICIENT_DATA",
                "EARLY_SIGNAL",
            }


def test_outreach_performance_learnings_contract():
    response = client.get(
        "/api/outreach/performance"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["learnings"],
        list,
    )

    for learning in data["learnings"]:
        assert "dimension" in learning
        assert "segment" in learning
        assert "status" in learning
        assert "message" in learning
        assert "metrics" in learning

        assert learning["status"] in {
            "INSUFFICIENT_DATA",
            "EARLY_SIGNAL",
        }

        assert (
            learning["metrics"]["segment"]
            == learning["segment"]
        )
