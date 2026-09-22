import csv
from pathlib import Path
from typing import List

from app.providers.signals.base import (
    SignalProvider,
)
from app.schemas.signal import SignalCreate


class CSVSignalProvider(SignalProvider):
    """
    Load evidence-backed company signals from CSV.

    Expected columns:
    Company Name
    Signal Type
    Title
    Description
    Source
    Source URL
    Signal Date
    Confidence
    """

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    @staticmethod
    def _clean(value):
        if value is None:
            return None

        cleaned = str(value).strip()

        return cleaned or None

    @staticmethod
    def _normalise_company_name(
        value: str,
    ) -> str:
        return " ".join(
            value.lower().split()
        )

    def discover_signals(
        self,
        company: dict,
    ) -> List[SignalCreate]:
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Signal CSV not found: "
                f"{self.csv_path}"
            )

        company_name = (
            self._normalise_company_name(
                company["name"]
            )
        )

        signals = []

        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            for row in reader:
                row_company = self._clean(
                    row.get("Company Name")
                )

                if not row_company:
                    continue

                if (
                    self._normalise_company_name(
                        row_company
                    )
                    != company_name
                ):
                    continue

                signal_type = self._clean(
                    row.get("Signal Type")
                )
                title = self._clean(
                    row.get("Title")
                )
                source = self._clean(
                    row.get("Source")
                )
                confidence = (
                    self._clean(
                        row.get("Confidence")
                    )
                    or "MEDIUM"
                )

                # Evidence-bearing fields are required.
                # We do not ingest vague or untraceable
                # signal rows.
                source_url = self._clean(
                    row.get("Source URL")
                )
                signal_date = self._clean(
                    row.get("Signal Date")
                )

                if not all(
                    [
                        signal_type,
                        title,
                        source,
                        source_url,
                        signal_date,
                    ]
                ):
                    continue

                signals.append(
                    SignalCreate(
                        signal_type=signal_type,
                        title=title,
                        description=self._clean(
                            row.get("Description")
                        ),
                        source=source,
                        source_url=source_url,
                        signal_date=signal_date,
                        confidence=confidence,
                    )
                )

        return signals
