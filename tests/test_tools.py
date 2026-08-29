from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.anomaly_tool import AnomalyTool
from app.tools.batch_prediction_tool import BatchPredictionTool
from app.tools.customer_history_tool import CustomerHistoryTool
from app.tools.decision_tool import DecisionTool
from app.tools.prediction_tool import (
    PredictionToolError,
    check_ml_service,
    predict_transaction,
)
from app.tools.transaction_tool import (
    TransactionTool,
    TransactionToolError,
)
from app.tools.velocity_tool import VelocityTool


# ============================================================
# Shared test data
# ============================================================

TRANSACTION = {
    "transaction_id": "TEST_TXN_001",
    "customer_id": "TEST_CUSTOMER_001",
    "amount": 1000.0,
    "currency": "INR",
    "merchant_id": "M001",
    "merchant_category": "retail",
    "transaction_type": "purchase",
    "channel": "online",
    "location": "IN",
    "device_id": "DEVICE_001",
}


# ============================================================
# TransactionTool
# ============================================================


def test_transaction_tool_analyze_transaction():
    repository = MagicMock()

    tool = TransactionTool(repository)

    result = tool.analyze_transaction(
        TRANSACTION
    )

    assert result["transaction_id"] == "TEST_TXN_001"
    assert result["customer_id"] == "TEST_CUSTOMER_001"
    assert result["amount"] == 1000.0
    assert result["currency"] == "INR"

    assert result["merchant_id"] == "M001"
    assert result["merchant_category"] == "retail"
    assert result["transaction_type"] == "purchase"
    assert result["channel"] == "online"
    assert result["location"] == "IN"

    assert result["high_amount"] is False
    assert result["has_device_id"] is True
    assert result["has_location"] is True


def test_transaction_tool_high_amount():
    repository = MagicMock()

    tool = TransactionTool(repository)

    transaction = {
        **TRANSACTION,
        "amount": 50000,
    }

    result = tool.analyze_transaction(
        transaction
    )

    assert result["high_amount"] is True


def test_transaction_tool_get_transaction():
    repository = MagicMock()

    repository.get_transaction.return_value = TRANSACTION

    tool = TransactionTool(repository)

    result = tool.get_transaction(
        "TEST_TXN_001"
    )

    repository.get_transaction.assert_called_once_with(
        "TEST_TXN_001"
    )

    assert result == TRANSACTION


def test_transaction_tool_missing_transaction():
    repository = MagicMock()

    repository.get_transaction.return_value = None

    tool = TransactionTool(repository)

    with pytest.raises(
        TransactionToolError,
        match="Transaction 'UNKNOWN' not found",
    ):
        tool.get_transaction("UNKNOWN")


# ============================================================
# CustomerHistoryTool
# ============================================================


def test_customer_history_without_history():
    repository = MagicMock()

    repository.get_customer_transactions.return_value = []

    tool = CustomerHistoryTool(repository)

    result = tool.analyze_customer(
        customer_id="TEST_CUSTOMER_001",
        current_amount=1000.0,
    )

    assert result["customer_id"] == "TEST_CUSTOMER_001"
    assert result["transaction_count"] == 0
    assert result["average_amount"] == 0.0
    assert result["maximum_amount"] == 0.0
    assert result["current_amount"] == 1000.0
    assert result["customer_risk"] == 0.5
    assert result["history_available"] is False


def test_customer_history_with_normal_transaction():
    repository = MagicMock()

    repository.get_customer_transactions.return_value = [
        {"amount": 1000},
        {"amount": 2000},
        {"amount": 3000},
    ]

    tool = CustomerHistoryTool(repository)

    result = tool.analyze_customer(
        customer_id="TEST_CUSTOMER_001",
        current_amount=2000.0,
    )

    assert result["transaction_count"] == 3
    assert result["average_amount"] == 2000.0
    assert result["maximum_amount"] == 3000.0
    assert result["current_amount"] == 2000.0
    assert result["amount_ratio"] == 1.0
    assert result["customer_risk"] == 0.20
    assert result["history_available"] is True


def test_customer_history_high_amount_ratio():
    repository = MagicMock()

    repository.get_customer_transactions.return_value = [
        {"amount": 1000},
        {"amount": 1000},
    ]

    tool = CustomerHistoryTool(repository)

    result = tool.analyze_customer(
        customer_id="TEST_CUSTOMER_001",
        current_amount=10000.0,
    )

    assert result["amount_ratio"] == 10.0
    assert result["customer_risk"] == 0.90


# ============================================================
# VelocityTool
# ============================================================


def test_velocity_tool_low_velocity():
    repository = MagicMock()

    repository.count_recent_transactions.side_effect = [
        0,
        0,
    ]

    tool = VelocityTool(repository)

    timestamp = datetime.now(timezone.utc)

    result = tool.analyze_velocity(
        customer_id="TEST_CUSTOMER_001",
        timestamp=timestamp,
    )

    assert result["transactions_last_5_minutes"] == 0
    assert result["transactions_last_60_minutes"] == 0
    assert result["velocity_risk"] == 0.10
    assert result["velocity_anomaly"] is False


def test_velocity_tool_high_velocity():
    repository = MagicMock()

    repository.count_recent_transactions.side_effect = [
        5,
        10,
    ]

    tool = VelocityTool(repository)

    timestamp = datetime.now(timezone.utc)

    result = tool.analyze_velocity(
        customer_id="TEST_CUSTOMER_001",
        timestamp=timestamp,
    )

    assert result["transactions_last_5_minutes"] == 5
    assert result["transactions_last_60_minutes"] == 10
    assert result["velocity_risk"] == 0.95
    assert result["velocity_anomaly"] is True


# ============================================================
# AnomalyTool
# ============================================================


def test_anomaly_tool_no_anomaly():
    tool = AnomalyTool()

    transaction_analysis = {
        "high_amount": False,
    }

    customer_history = {
        "amount_ratio": 1.0,
    }

    velocity = {
        "velocity_anomaly": False,
    }

    result = tool.analyze(
        transaction_analysis,
        customer_history,
        velocity,
    )

    assert result["anomaly_detected"] is False
    assert result["anomaly_score"] == 0.10
    assert result["triggered_anomalies"] == []


def test_anomaly_tool_multiple_anomalies():
    tool = AnomalyTool()

    transaction_analysis = {
        "high_amount": True,
    }

    customer_history = {
        "amount_ratio": 10.0,
    }

    velocity = {
        "velocity_anomaly": True,
    }

    result = tool.analyze(
        transaction_analysis,
        customer_history,
        velocity,
    )

    assert result["anomaly_detected"] is True
    assert result["anomaly_score"] == 0.95

    assert len(
        result["triggered_anomalies"]
    ) == 3

    assert (
        "AMOUNT_SIGNIFICANTLY_ABOVE_CUSTOMER_BASELINE"
        in result["triggered_anomalies"]
    )

    assert (
        "HIGH_TRANSACTION_VELOCITY"
        in result["triggered_anomalies"]
    )

    assert (
        "HIGH_VALUE_TRANSACTION"
        in result["triggered_anomalies"]
    )


# ============================================================
# DecisionTool
# ============================================================


def test_decision_tool_low_risk():
    tool = DecisionTool()

    result = tool.evaluate(
        ml_probability=0.01,
        anomaly_detected=False,
        velocity_risk=0.10,
        customer_risk=0.20,
        transaction_risk=0.10,
    )

    assert result["risk_level"] == "LOW"
    assert result["action"] == "APPROVE"
    assert result["risk_score"] == 0.01

    assert "triggered_rules" in result
    assert "reason" in result


def test_decision_tool_high_risk():
    tool = DecisionTool()

    result = tool.evaluate(
        ml_probability=0.95,
        anomaly_detected=True,
        velocity_risk=0.95,
        customer_risk=0.90,
        transaction_risk=0.90,
    )

    assert result["risk_level"] == "CRITICAL"
    assert result["action"] == "BLOCK"

    assert result["risk_score"] >= 0.95
    assert len(result["triggered_rules"]) > 0


# ============================================================
# PredictionTool
# ============================================================


@pytest.mark.asyncio
async def test_prediction_tool_success():

    mock_response = MagicMock()

    mock_response.status_code = 200

    mock_response.json.return_value = {
        "model": "AI-Risk-Manager-XGBoost",
        "alias": "champion",
        "fraud_probability": 0.01,
        "threshold": 0.48,
        "prediction": 0,
        "label": "Legitimate",
    }

    mock_client = AsyncMock()

    mock_client.post.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    with patch(
        "app.tools.prediction_tool.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "app.tools.prediction_tool.get_ml_service_url",
        return_value="http://ml-service",
    ):

        result = await predict_transaction(
            TRANSACTION
        )

    assert result["model"] == "AI-Risk-Manager-XGBoost"
    assert result["alias"] == "champion"
    assert result["fraud_probability"] == 0.01
    assert result["threshold"] == 0.48
    assert result["prediction"] == 0
    assert result["label"] == "Legitimate"

    mock_client.post.assert_called_once_with(
        "http://ml-service/predict",
        json={
            "transaction": TRANSACTION
        },
    )


@pytest.mark.asyncio
async def test_prediction_tool_empty_transaction():

    with pytest.raises(
        PredictionToolError,
        match="Transaction data cannot be empty",
    ):
        await predict_transaction({})


@pytest.mark.asyncio
async def test_prediction_tool_invalid_probability():

    mock_response = MagicMock()

    mock_response.status_code = 200

    mock_response.json.return_value = {
        "model": "AI-Risk-Manager-XGBoost",
        "alias": "champion",
        "fraud_probability": 2.0,
        "threshold": 0.48,
        "prediction": 1,
        "label": "Fraud",
    }

    mock_client = AsyncMock()

    mock_client.post.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    with patch(
        "app.tools.prediction_tool.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "app.tools.prediction_tool.get_ml_service_url",
        return_value="http://ml-service",
    ):

        with pytest.raises(
            PredictionToolError,
            match="invalid fraud probability",
        ):
            await predict_transaction(
                TRANSACTION
            )


@pytest.mark.asyncio
async def test_prediction_tool_http_error():

    mock_response = MagicMock()

    mock_response.status_code = 500

    mock_response.json.return_value = {
        "detail": "Internal server error"
    }

    mock_client = AsyncMock()

    mock_client.post.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    with patch(
        "app.tools.prediction_tool.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "app.tools.prediction_tool.get_ml_service_url",
        return_value="http://ml-service",
    ):

        with pytest.raises(
            PredictionToolError,
            match="ML prediction failed",
        ):
            await predict_transaction(
                TRANSACTION
            )


@pytest.mark.asyncio
async def test_check_ml_service_success():

    mock_response = MagicMock()

    mock_response.status_code = 200

    mock_client = AsyncMock()

    mock_client.get.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    with patch(
        "app.tools.prediction_tool.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "app.tools.prediction_tool.get_ml_service_url",
        return_value="http://ml-service",
    ):

        result = await check_ml_service()

    assert result is True


# ============================================================
# BatchPredictionTool
# ============================================================


def test_batch_prediction_tool_endpoint():

    tool = BatchPredictionTool(
        ml_service_url="http://ml-service"
    )

    assert (
        tool.endpoint
        == "http://ml-service/predict/batch"
    )


@pytest.mark.asyncio
async def test_batch_prediction_tool_missing_file(
    tmp_path,
):

    tool = BatchPredictionTool(
        ml_service_url="http://ml-service"
    )

    result = await tool.analyze_csv(
        tmp_path / "missing.csv"
    )

    assert result["success"] is False
    assert result["data"] == {}
    assert "File not found" in result["error"]


@pytest.mark.asyncio
async def test_batch_prediction_tool_invalid_file_type(
    tmp_path,
):

    file_path = tmp_path / "test.txt"

    file_path.write_text(
        "test",
        encoding="utf-8",
    )

    tool = BatchPredictionTool(
        ml_service_url="http://ml-service"
    )

    result = await tool.analyze_csv(
        file_path
    )

    assert result["success"] is False
    assert result["data"] == {}
    assert (
        result["error"]
        == "Only CSV files are supported."
    )


@pytest.mark.asyncio
async def test_batch_prediction_tool_success(
    tmp_path,
):

    file_path = tmp_path / "transactions.csv"

    file_path.write_text(
        "transaction_id,amount\n"
        "TXN001,1000\n",
        encoding="utf-8",
    )

    mock_response = MagicMock()

    mock_response.status_code = 200

    mock_response.json.return_value = {
        "job_id": "TEST_JOB_001",
        "created_at": "2026-08-29T00:00:00+00:00",
        "model": "AI-Risk-Manager-XGBoost",
        "alias": "champion",
        "model_version": 11,
        "total_transactions": 1,
        "fraud_transactions": 0,
        "legitimate_transactions": 1,
        "fraud_rate": 0.0,
        "average_fraud_probability": 0.01,
        "production_threshold": 0.48,
        "result_download_url": (
            "https://example.com/predictions.csv"
        ),
        "report_download_url": (
            "https://example.com/report.json"
        ),
    }

    mock_client = AsyncMock()

    mock_client.post.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    with patch(
        "app.tools.batch_prediction_tool.httpx.AsyncClient",
        return_value=mock_context,
    ):

        tool = BatchPredictionTool(
            ml_service_url="http://ml-service"
        )

        result = await tool.analyze_csv(
            file_path=file_path,
            filename="transactions.csv",
        )

    assert result["success"] is True
    assert result["error"] is None

    data = result["data"]

    assert data["job_id"] == "TEST_JOB_001"
    assert data["total_transactions"] == 1
    assert data["fraud_transactions"] == 0
    assert data["legitimate_transactions"] == 1
    assert data["fraud_rate"] == 0.0
    assert data["production_threshold"] == 0.48

    assert "result_download_url" in data
    assert "report_download_url" in data

    mock_client.post.assert_called_once()


# ============================================================
# Tool integration sanity check
# ============================================================


def test_tools_can_be_constructed():

    repository = MagicMock()

    transaction_tool = TransactionTool(
        repository
    )

    customer_history_tool = CustomerHistoryTool(
        repository
    )

    velocity_tool = VelocityTool(
        repository
    )

    anomaly_tool = AnomalyTool()

    decision_tool = DecisionTool()

    assert transaction_tool is not None
    assert customer_history_tool is not None
    assert velocity_tool is not None
    assert anomaly_tool is not None
    assert decision_tool is not None