from pathlib import Path

from app.config import (
    DEFAULT_CLAY_COMPANY_CSV_PATH,
    get_clay_company_csv_path,
)


def test_clay_company_csv_path_uses_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "CLAY_COMPANY_CSV_PATH",
        raising=False,
    )

    assert get_clay_company_csv_path() == Path(
        DEFAULT_CLAY_COMPANY_CSV_PATH
    )


def test_clay_company_csv_path_can_be_overridden(
    monkeypatch,
):
    monkeypatch.setenv(
        "CLAY_COMPANY_CSV_PATH",
        "/tmp/new-clay-export.csv",
    )

    assert get_clay_company_csv_path() == Path(
        "/tmp/new-clay-export.csv"
    )
