from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_valid_clay_csv(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "clay_companies.csv"

    monkeypatch.setenv(
        "CLAY_COMPANY_CSV_PATH",
        str(destination),
    )

    csv_content = (
        "Name,Domain,Country,Industry,Size\n"
        "Test Logistics,test-logistics.example,"
        "India,Logistics,501-1000\n"
    )

    response = client.post(
        "/api/companies/upload-clay-csv",
        files={
            "file": (
                "companies.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "uploaded"
    assert data["filename"] == "companies.csv"
    assert data["rows_received"] == 1
    assert destination.exists()

    saved_content = destination.read_text()

    assert "Test Logistics" in saved_content
    assert "test-logistics.example" in saved_content


def test_upload_rejects_non_csv(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "clay_companies.csv"

    monkeypatch.setenv(
        "CLAY_COMPANY_CSV_PATH",
        str(destination),
    )

    response = client.post(
        "/api/companies/upload-clay-csv",
        files={
            "file": (
                "companies.txt",
                "Name,Domain\nTest,test.example\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only CSV files are accepted."
    )

    assert not destination.exists()


def test_upload_rejects_missing_domain_without_overwrite(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "clay_companies.csv"

    monkeypatch.setenv(
        "CLAY_COMPANY_CSV_PATH",
        str(destination),
    )

    original_content = (
        "Name,Domain\n"
        "Existing Company,existing.example\n"
    )

    destination.write_text(original_content)

    invalid_csv = (
        "Name,Country,Industry\n"
        "Broken Logistics,India,Logistics\n"
    )

    response = client.post(
        "/api/companies/upload-clay-csv",
        files={
            "file": (
                "broken.csv",
                invalid_csv,
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Clay CSV is missing required columns: domain"
    )

    assert destination.read_text() == original_content


def test_upload_rejects_empty_csv(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "clay_companies.csv"

    monkeypatch.setenv(
        "CLAY_COMPANY_CSV_PATH",
        str(destination),
    )

    response = client.post(
        "/api/companies/upload-clay-csv",
        files={
            "file": (
                "empty.csv",
                "",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Uploaded CSV is empty."
    )

    assert not destination.exists()
