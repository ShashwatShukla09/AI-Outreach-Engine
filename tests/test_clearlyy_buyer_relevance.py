import pytest

from app.services.buyer_relevance_service import (
    find_best_buyer_match,
)


BUYER_CATEGORIES = [
    "Operations",
    "Learning and Development",
    "Training",
    "Human Resources",
    "People",
    "Workforce Enablement",
    "Safety and Compliance",
]


@pytest.mark.parametrize(
    "job_title,expected_category",
    [
        ("Head of Operations", "Operations"),
        ("VP Operations", "Operations"),
        ("Director of Operations", "Operations"),
        (
            "Head of Learning & Development",
            "Learning and Development",
        ),
        (
            "L&D Manager",
            "Learning and Development",
        ),
        ("Head of Training", "Training"),
        ("Training Manager", "Training"),
        ("CHRO", "Human Resources"),
        ("Head of HR", "Human Resources"),
        ("Chief People Officer", "People"),
        (
            "Head of Workforce Enablement",
            "Workforce Enablement",
        ),
        (
            "Head of Capability Development",
            "Workforce Enablement",
        ),
        (
            "Head of Safety",
            "Safety and Compliance",
        ),
        (
            "EHS Head",
            "Safety and Compliance",
        ),
    ],
)
def test_clearlyy_buyer_titles_match(
    job_title,
    expected_category,
):
    category, score, _ = find_best_buyer_match(
        job_title=job_title,
        buyer_categories=BUYER_CATEGORIES,
    )

    assert category == expected_category
    assert score == 10


def test_irrelevant_title_does_not_match():
    category, score, _ = find_best_buyer_match(
        job_title="Marketing Manager",
        buyer_categories=BUYER_CATEGORIES,
    )

    assert category is None
    assert score == 0
