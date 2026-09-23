import os
from pathlib import Path


DEFAULT_CLAY_COMPANY_CSV_PATH = (
    "data/imports/clearlyy_india_logistics.csv"
)


def get_clay_company_csv_path() -> Path:
    configured_path = os.getenv(
        "CLAY_COMPANY_CSV_PATH",
        DEFAULT_CLAY_COMPANY_CSV_PATH,
    )

    return Path(configured_path).expanduser()
