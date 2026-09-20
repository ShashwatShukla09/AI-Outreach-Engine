import json
from typing import Any, Dict

import httpx
from pydantic import ValidationError

from app.providers.llm.base import ICPProvider
from app.schemas.icp import (
    ICPDefinition,
    ICPGenerationResult,
)
from app.schemas.product import ProductResponse


class OllamaICPProvider(ICPProvider):
    """
    Generate structured ICPs using a locally running Ollama model.
    """

    def __init__(
        self,
        model: str = "llama3:8b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate_icps(
        self,
        product: ProductResponse,
    ) -> ICPGenerationResult:
        prompt = self._build_prompt(product)

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": self._output_schema(),
                "options": {
                    "temperature": 0.1,
                },
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        ollama_data = response.json()
        raw_output = ollama_data.get("response")

        if not raw_output:
            raise ValueError(
                "Ollama returned an empty response."
            )

        try:
            parsed_output = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Ollama returned invalid JSON."
            ) from exc

        return self._validate_result(
            product_id=product.id,
            parsed_output=parsed_output,
        )

    def _output_schema(self) -> Dict[str, Any]:
        """
        JSON schema sent directly to Ollama.

        This constrains the model to the structure our
        application expects.
        """

        icp_schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "industries": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "company_size_min": {
                    "type": "integer",
                },
                "company_size_max": {
                    "type": "integer",
                },
                "target_market": {
                    "type": "string",
                    "enum": [
                        "INDIA",
                        "INTERNATIONAL",
                    ],
                },
                "target_countries": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "business_models": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "buyer_categories": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "pain_points": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "segment_rationale": {
                    "type": "string",
                },
                "buyer_rationale": {
                    "type": "string",
                },
                "assumptions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": [
                "name",
                "industries",
                "company_size_min",
                "company_size_max",
                "target_market",
                "target_countries",
                "business_models",
                "buyer_categories",
                "pain_points",
                "segment_rationale",
                "buyer_rationale",
                "assumptions",
            ],
        }

        return {
            "type": "object",
            "properties": {
                "icps": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": icp_schema,
                },
            },
            "required": [
                "icps",
            ],
        }

    def _build_prompt(
        self,
        product: ProductResponse,
    ) -> str:
        return f"""
You are a B2B go-to-market research assistant.

Analyse the product below and generate exactly two
ideal customer profiles.

PRODUCT

Name:
{product.name}

Description:
{product.description}

Value proposition:
{product.value_proposition or "Not provided"}

Target problem:
{product.target_problem or "Not provided"}


REQUIRED MARKETS

Generate exactly:

1. One INDIA ICP.
2. One INTERNATIONAL ICP.


REASONING REQUIREMENTS

For each ICP determine:

- commercially plausible industries
- realistic company-size range
- relevant business models
- likely buyer roles
- pain points directly connected to the product
- why this segment is appropriate
- why these buyer roles are relevant
- assumptions that would need later verification


IMPORTANT RULES

- Base the ICP primarily on the supplied product information.
- Do not invent evidence about specific companies.
- Put uncertain claims in assumptions.
- Pain points must connect directly to the target problem.
- Buyer categories must contain job roles, not people's names.
- Business models describe how the TARGET COMPANY operates.
- Business models do not describe how this product is priced.
- Do not create artificial differences between India and
  international markets.
- The two markets may share industries when commercially logical.
- company_size_min must not exceed company_size_max.
- INDIA must use target_market "INDIA".
- INTERNATIONAL must use target_market "INTERNATIONAL".
- India must appear in the INDIA target countries.
- Return exactly two ICPs.
- Follow the supplied JSON schema exactly.
"""

    def _validate_result(
        self,
        product_id: int,
        parsed_output: Dict[str, Any],
    ) -> ICPGenerationResult:
        raw_icps = parsed_output.get("icps")

        if not isinstance(raw_icps, list):
            raise ValueError(
                "Ollama response does not contain an ICP list."
            )

        if len(raw_icps) != 2:
            raise ValueError(
                "Ollama must return exactly two ICPs."
            )

        try:
            icps = [
                ICPDefinition(**raw_icp)
                for raw_icp in raw_icps
            ]
        except ValidationError as exc:
            raise ValueError(
                "Ollama returned an invalid ICP structure."
            ) from exc

        markets = {
            icp.target_market
            for icp in icps
        }

        if markets != {
            "INDIA",
            "INTERNATIONAL",
        }:
            raise ValueError(
                "Ollama must return one INDIA and "
                "one INTERNATIONAL ICP."
            )

        for icp in icps:
            if (
                icp.company_size_min
                > icp.company_size_max
            ):
                raise ValueError(
                    "ICP minimum company size cannot "
                    "exceed maximum company size."
                )

        india_icp = next(
            icp
            for icp in icps
            if icp.target_market == "INDIA"
        )

        if "India" not in india_icp.target_countries:
            raise ValueError(
                "INDIA ICP must include India "
                "in target countries."
            )

        return ICPGenerationResult(
            product_id=product_id,
            icps=icps,
        )
