from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_product():
    payload = {
        "name": "Test AI Product",
        "description": (
            "AI software that helps teams automate "
            "repetitive operational work."
        ),
        "value_proposition": (
            "Reduce manual work and improve operational efficiency."
        ),
        "target_problem": (
            "Teams spend too much time on repetitive manual processes."
        ),
    }

    response = client.post(
        "/products",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "Test AI Product"
    assert data["description"] == payload["description"]
    assert data["value_proposition"] == payload["value_proposition"]
    assert data["target_problem"] == payload["target_problem"]
    assert "created_at" in data


def test_get_product():
    create_response = client.post(
        "/products",
        json={
            "name": "Retrievable Product",
            "description": (
                "A sufficiently detailed description "
                "for testing product retrieval."
            ),
            "value_proposition": "Help teams work more efficiently.",
            "target_problem": "Too much repetitive manual work.",
        },
    )

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Retrievable Product"


def test_missing_product_returns_404():
    response = client.get(
        "/products/999999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found"
    }


def test_product_name_validation():
    response = client.post(
        "/products",
        json={
            "name": "A",
            "description": (
                "This description is long enough "
                "to satisfy validation."
            ),
        },
    )

    assert response.status_code == 422


def test_product_description_validation():
    response = client.post(
        "/products",
        json={
            "name": "Valid Product",
            "description": "Short",
        },
    )

    assert response.status_code == 422
