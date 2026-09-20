import pytest

from app.providers.llm.mock_provider import MockICPProvider
from app.schemas.icp import ICPUpdate
from app.schemas.product import ProductCreate
from app.services.icp_service import (
    approve_icp,
    edit_icp,
    generate_and_save_icps,
    reject_icp,
)
from app.services.product_service import create_new_product


def create_test_icps():
    product = create_new_product(
        ProductCreate(
            name="Lifecycle Test Product",
            description=(
                "AI software that helps customer support "
                "teams answer repetitive questions."
            ),
            value_proposition=(
                "Reduce repetitive support work."
            ),
            target_problem=(
                "Support teams spend too much time "
                "answering repeated questions."
            ),
        )
    )

    return generate_and_save_icps(
        product_id=product["id"],
        provider=MockICPProvider(),
    )


def test_draft_icp_can_be_edited():
    icps = create_test_icps()
    icp = icps[0]

    updated = edit_icp(
        icp.id,
        ICPUpdate(
            company_size_min=50,
            buyer_categories=[
                "Head of Customer Experience",
                "Customer Support Manager",
            ],
        ),
    )

    assert updated.company_size_min == 50
    assert (
        "Head of Customer Experience"
        in updated.buyer_categories
    )
    assert updated.status == "DRAFT"


def test_draft_icp_can_be_approved():
    icps = create_test_icps()
    icp = icps[0]

    approved = approve_icp(icp.id)

    assert approved.status == "APPROVED"
    assert approved.reviewed_at is not None


def test_approved_icp_cannot_be_edited():
    icps = create_test_icps()
    icp = icps[0]

    approve_icp(icp.id)

    with pytest.raises(
        ValueError,
        match="Only DRAFT ICPs can be edited",
    ):
        edit_icp(
            icp.id,
            ICPUpdate(company_size_min=10),
        )


def test_draft_icp_can_be_rejected():
    icps = create_test_icps()
    icp = icps[1]

    rejected = reject_icp(icp.id)

    assert rejected.status == "REJECTED"
    assert rejected.reviewed_at is not None


def test_invalid_company_size_update_is_rejected():
    icps = create_test_icps()
    icp = icps[0]

    with pytest.raises(
        ValueError,
        match=(
            "Minimum company size cannot exceed "
            "maximum company size"
        ),
    ):
        edit_icp(
            icp.id,
            ICPUpdate(
                company_size_min=1000,
                company_size_max=100,
            ),
        )
