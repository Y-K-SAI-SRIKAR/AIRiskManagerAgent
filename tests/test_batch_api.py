import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_batch_analysis_api():

    csv_path = "tests/test_transactions.csv"

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:

        with open(csv_path, "rb") as file:

            response = await client.post(
                "/analyze/batch",
                files={
                    "file": (
                        "test_transactions.csv",
                        file,
                        "text/csv",
                    )
                },
            )

    print(
        "\n================ BATCH API RESPONSE ================\n"
    )

    print(f"HTTP Status: {response.status_code}")
    print(response.json())

    print(
        "\n======================================================\n"
    )

    # --------------------------------------------------
    # HTTP response
    # --------------------------------------------------

    assert response.status_code == 200

    body = response.json()

    # --------------------------------------------------
    # Top-level response
    # --------------------------------------------------

    assert body["success"] is True
    assert body["job_id"]
    assert body["status"] == "completed"

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    summary = body["summary"]

    assert summary["total_transactions"] == 10
    assert "fraud_transactions" in summary
    assert "legitimate_transactions" in summary
    assert "fraud_rate" in summary
    assert "average_fraud_probability" in summary
    assert "production_threshold" in summary

    # --------------------------------------------------
    # Model metadata
    # --------------------------------------------------

    model = body["model"]

    assert model["name"] == "AI-Risk-Manager-XGBoost"
    assert model["alias"] == "champion"
    assert model["version"] is not None

    # --------------------------------------------------
    # S3 artifacts
    # --------------------------------------------------

    artifacts = body["artifacts"]

    assert artifacts["result_download_url"]
    assert artifacts["report_download_url"]

    assert "predictions.csv" in artifacts[
        "result_download_url"
    ]

    assert "report.json" in artifacts[
        "report_download_url"
    ]