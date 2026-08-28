import pytest

from app.tools.batch_prediction_tool import BatchPredictionTool


@pytest.mark.asyncio
async def test_batch_prediction_tool():

    tool = BatchPredictionTool()

    result = await tool.analyze_csv(
        "tests/test_transactions.csv"
    )

    print(
        "\n================ BATCH TOOL RESPONSE ================\n"
    )

    print(result)

    print(
        "\n======================================================\n"
    )

    assert "success" in result

    if result["success"]:

        assert "data" in result
        assert "error" in result

        data = result["data"]

        assert "job_id" in data
        assert "total_transactions" in data
        assert "fraud_transactions" in data
        assert "legitimate_transactions" in data
        assert "fraud_rate" in data
        assert "result_download_url" in data
        assert "report_download_url" in data