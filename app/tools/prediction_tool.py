import os
from typing import Any, Dict

import httpx


DEFAULT_TIMEOUT = 30.0


class PredictionToolError(Exception):
    """
    Raised when the ML prediction service cannot be used.
    """


def get_ml_service_url() -> str:

    url = os.getenv(
        "ML_SERVICE_URL",
        "http://localhost:8001",
    )

    return url.rstrip("/")


async def predict_transaction(
    transaction: Dict[str, Any],
) -> Dict[str, Any]:

    if not transaction:
        raise PredictionToolError(
            "Transaction data cannot be empty."
        )

    url = f"{get_ml_service_url()}/predict"

    payload = {
        "transaction": transaction
    }

    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT
        ) as client:

            response = await client.post(
                url,
                json=payload,
            )

    except httpx.TimeoutException as exc:
        raise PredictionToolError(
            "ML prediction service timed out."
        ) from exc

    except httpx.RequestError as exc:
        raise PredictionToolError(
            f"Unable to connect to ML prediction service: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            detail = response.json()

        except ValueError:
            detail = response.text

        raise PredictionToolError(
            f"ML prediction failed "
            f"(HTTP {response.status_code}): {detail}"
        )

    try:
        result = response.json()

    except ValueError as exc:
        raise PredictionToolError(
            "ML prediction service returned invalid JSON."
        ) from exc

    _validate_prediction_response(result)

    return result


def _validate_prediction_response(
    result: Dict[str, Any],
) -> None:
    """
    Validate the response returned by the ML service.
    """

    required_fields = {
        "model",
        "alias",
        "fraud_probability",
        "threshold",
        "prediction",
        "label",
    }

    missing = required_fields - result.keys()

    if missing:
        raise PredictionToolError(
            "ML service response is missing fields: "
            + ", ".join(sorted(missing))
        )

    probability = float(
        result["fraud_probability"]
    )

    if not 0.0 <= probability <= 1.0:
        raise PredictionToolError(
            "ML service returned an invalid fraud probability: "
            f"{probability}"
        )

async def check_ml_service() -> bool:
    """
    Check whether the deployed ML service is available.
    """

    url = f"{get_ml_service_url()}/health"

    try:
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            response = await client.get(url)

        return response.status_code == 200

    except httpx.RequestError:
        return False