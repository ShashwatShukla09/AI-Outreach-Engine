import pytest
from pydantic import ValidationError

from app.schemas.icp import ICPDefinition


def make_valid_icp(**overrides):
    data = {
        "name": "Support Automation ICP",
        "industries": ["SaaS"],
        "company_size_min": 20,
        "company_size_max": 200,
        "target_market": "INDIA",
        "target_countries": ["India"],
        "business_models": ["B2B SaaS"],
        "buyer_categories": ["Head of Support"],
        "pain_points": [
            "High repetitive support workload",
        ],
        "segment_rationale": (
            "Support-heavy businesses can benefit "
            "from automating repetitive questions."
        ),
        "buyer_rationale": (
            "The Head of Support is responsible "
            "for support operations and performance."
        ),
        "assumptions": [
            "The company handles repetitive support questions.",
        ],
    }

    data.update(overrides)

    return ICPDefinition(**data)


def test_valid_india_icp():
    icp = make_valid_icp()

    assert icp.target_market == "INDIA"
    assert icp.company_size_min == 20


def test_valid_international_icp():
    icp = make_valid_icp(
        target_market="INTERNATIONAL",
        target_countries=[
            "United Kingdom",
            "United States",
        ],
    )

    assert icp.target_market == "INTERNATIONAL"


def test_invalid_market_rejected():
    with pytest.raises(ValidationError):
        make_valid_icp(
            target_market="MARS",
        )
