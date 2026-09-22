from app.services.buyer_ranking_service import (
    rank_buyer,
    rank_company_buyers,
)


def test_direct_ld_owner_outranks_svp_operations():
    contacts = [
        {
            "id": 1,
            "first_name": "Operations",
            "last_name": "Buyer",
            "job_title": (
                "Senior Vice President, UTR Operations"
            ),
            "buyer_category": "Operations",
            "relevance_score": 10,
        },
        {
            "id": 2,
            "first_name": "Learning",
            "last_name": "Buyer",
            "job_title": (
                "Head of Learning & Development"
            ),
            "buyer_category": (
                "Learning and Development"
            ),
            "relevance_score": 10,
        },
    ]

    ranked = rank_company_buyers(contacts)

    assert ranked[0]["first_name"] == "Learning"
    assert ranked[0]["buyer_rank_score"] == 94
    assert ranked[0]["rank_label"] == "PRIMARY"

    assert ranked[1]["first_name"] == "Operations"
    assert ranked[1]["buyer_rank_score"] == 78


def test_svp_operations_outranks_vp_operations():
    contacts = [
        {
            "id": 1,
            "first_name": "VP",
            "last_name": "Buyer",
            "job_title": "Vice President Operations",
            "buyer_category": "Operations",
            "relevance_score": 10,
        },
        {
            "id": 2,
            "first_name": "SVP",
            "last_name": "Buyer",
            "job_title": (
                "Senior Vice President, UTR Operations"
            ),
            "buyer_category": "Operations",
            "relevance_score": 10,
        },
    ]

    ranked = rank_company_buyers(contacts)

    assert ranked[0]["first_name"] == "SVP"
    assert ranked[0]["buyer_rank_score"] == 78

    assert ranked[1]["first_name"] == "VP"
    assert ranked[1]["buyer_rank_score"] == 76


def test_non_relevant_contact_cannot_be_primary():
    contact = {
        "id": 1,
        "job_title": "Marketing Manager",
        "buyer_category": None,
        "relevance_score": 0,
    }

    ranking = rank_buyer(contact)

    assert ranking["buyer_rank_score"] == 0
    assert ranking["rank_label"] == "NOT_RELEVANT"


def test_training_head_is_primary_candidate():
    contact = {
        "id": 1,
        "job_title": "Head of Training",
        "buyer_category": "Training",
        "relevance_score": 10,
    }

    ranking = rank_buyer(contact)

    assert ranking["buyer_rank_score"] == 89
    assert ranking["rank_label"] == "PRIMARY"
