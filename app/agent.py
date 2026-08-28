from datetime import datetime
from typing import Any, Dict, Optional

from app.decision.risk_rules import evaluate_risk
from app.schemas.request import TransactionRequest
from app.schemas.response import (
    RiskDecision,
    RiskEvidence,
    RiskManagerResponse,
    ToolResult,
)

from app.tools.anomaly_tool import AnomalyTool
from app.tools.customer_history_tool import CustomerHistoryTool
from app.tools.decision_tool import DecisionTool
from app.tools.prediction_tool import (
    PredictionToolError,
    predict_transaction,
)
from app.tools.transaction_tool import TransactionTool
from app.tools.velocity_tool import VelocityTool

from app.repositories.transaction_repository import (
    TransactionRepository,
)


class RiskManagerAgent:
    """
    Core orchestration layer for the AI Risk Manager.

    The Agent:
        1. Receives a transaction
        2. Calls the deployed ML prediction service
        3. Analyzes transaction behaviour
        4. Checks customer history
        5. Checks transaction velocity
        6. Detects anomalies
        7. Applies deterministic risk rules
        8. Produces a final risk decision

    The LLM is intentionally not used here yet.
    """

    def __init__(
        self,
        repository: Optional[TransactionRepository] = None,
    ):
        self.repository = (
            repository
            or TransactionRepository()
        )

        self.transaction_tool = (
            TransactionTool(self.repository)
        )

        self.customer_history_tool = (
            CustomerHistoryTool(self.repository)
        )

        self.velocity_tool = (
            VelocityTool(self.repository)
        )

        self.anomaly_tool = AnomalyTool()

        self.decision_tool = DecisionTool()

    async def analyze(
        self,
        request: TransactionRequest,
    ) -> RiskManagerResponse:
        """
        Execute the complete transaction risk analysis.
        """

        tool_results = []

        # ==========================================================
        # 1. Transaction Analysis
        # ==========================================================

        transaction = request.model_dump()

        transaction_analysis = (
            self.transaction_tool.analyze_transaction(
                transaction
            )
        )

        tool_results.append(
            ToolResult(
                tool_name="transaction_tool",
                success=True,
                data=transaction_analysis,
            )
        )

        # ==========================================================
        # 2. Customer History
        # ==========================================================

        customer_history = (
            self.customer_history_tool.analyze_customer(
                customer_id=request.customer_id,
                current_amount=request.amount,
            )
        )

        tool_results.append(
            ToolResult(
                tool_name="customer_history_tool",
                success=True,
                data=customer_history,
            )
        )

        # ==========================================================
        # 3. Velocity Analysis
        # ==========================================================

        velocity = (
            self.velocity_tool.analyze_velocity(
                customer_id=request.customer_id,
                timestamp=request.timestamp,
            )
        )

        tool_results.append(
            ToolResult(
                tool_name="velocity_tool",
                success=True,
                data=velocity,
            )
        )

        # ==========================================================
        # 4. Anomaly Detection
        # ==========================================================

        anomaly = self.anomaly_tool.analyze(
            transaction_analysis=transaction_analysis,
            customer_history=customer_history,
            velocity=velocity,
        )

        tool_results.append(
            ToolResult(
                tool_name="anomaly_tool",
                success=True,
                data=anomaly,
            )
        )

        # ==========================================================
        # 5. ML Prediction
        # ==========================================================

        try:
            ml_result = await predict_transaction(
                transaction=request.features,
            )

            tool_results.append(
                ToolResult(
                    tool_name="prediction_tool",
                    success=True,
                    data=ml_result,
                )
            )

        except PredictionToolError as exc:

            tool_results.append(
                ToolResult(
                    tool_name="prediction_tool",
                    success=False,
                    error=str(exc),
                )
            )

            return self._service_failure_response(
                request=request,
                tool_results=tool_results,
                error=str(exc),
            )

        # ==========================================================
        # 6. Extract ML probability
        # ==========================================================

        ml_probability = float(
            ml_result["fraud_probability"]
        )

        # ==========================================================
        # 7. Decision Engine
        # ==========================================================

        decision = self.decision_tool.evaluate(
            ml_probability=ml_probability,
            anomaly_detected=anomaly[
                "anomaly_detected"
            ],
            velocity_risk=velocity[
                "velocity_risk"
            ],
            customer_risk=customer_history[
                "customer_risk"
            ],
            transaction_risk=anomaly[
                "anomaly_score"
            ],
        )

        tool_results.append(
            ToolResult(
                tool_name="decision_tool",
                success=True,
                data=decision,
            )
        )

        # ==========================================================
        # 8. Build Evidence
        # ==========================================================

        evidence = RiskEvidence(
            ml_risk_score=ml_probability,
            anomaly_detected=anomaly[
                "anomaly_detected"
            ],
            velocity_risk=velocity[
                "velocity_risk"
            ],
            customer_risk=customer_history[
                "customer_risk"
            ],
            transaction_risk=anomaly[
                "anomaly_score"
            ],
            triggered_rules=decision[
                "triggered_rules"
            ],
        )

        # ==========================================================
        # 9. Build Decision
        # ==========================================================

        risk_decision = RiskDecision(
            risk_level=decision[
                "risk_level"
            ],
            action=decision[
                "action"
            ],
            confidence=ml_probability,
            reason=decision[
                "reason"
            ],
        )

        # ==========================================================
        # 10. Persist transaction
        # ==========================================================

        self.repository.add_transaction(
            transaction
        )

        # ==========================================================
        # 11. Final Response
        # ==========================================================

        explanation = self._build_explanation(
            request=request,
            ml_probability=ml_probability,
            customer_history=customer_history,
            velocity=velocity,
            anomaly=anomaly,
            decision=decision,
        )

        return RiskManagerResponse(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            success=True,
            decision=risk_decision,
            evidence=evidence,
            tool_results=tool_results,
            explanation=explanation,
            metadata={
                "ml_model": ml_result.get(
                    "model"
                ),
                "ml_alias": ml_result.get(
                    "alias"
                ),
                "ml_threshold": ml_result.get(
                    "threshold"
                ),
            },
        )

    # ==============================================================
    # Explanation
    # ==============================================================

    def _build_explanation(
        self,
        request: TransactionRequest,
        ml_probability: float,
        customer_history: Dict[str, Any],
        velocity: Dict[str, Any],
        anomaly: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> str:

        parts = [
            (
                f"The ML model assigned a fraud probability "
                f"of {ml_probability:.2%}."
            )
        ]

        if customer_history.get(
            "history_available"
        ):
            amount_ratio = customer_history.get(
                "amount_ratio",
                1.0,
            )

            parts.append(
                (
                    f"The current transaction amount is "
                    f"{amount_ratio:.2f}x the customer's "
                    f"historical average."
                )
            )

        if velocity.get(
            "velocity_anomaly"
        ):
            parts.append(
                (
                    "The transaction velocity is "
                    "considered elevated."
                )
            )

        if anomaly.get(
            "anomaly_detected"
        ):
            anomaly_count = len(
                anomaly.get(
                    "triggered_anomalies",
                    [],
                )
            )

            parts.append(
                (
                    f"{anomaly_count} behavioural "
                    f"anomaly indicator(s) were detected."
                )
            )

        parts.append(
            (
                f"The resulting risk level is "
                f"{decision['risk_level']} and the "
                f"recommended action is "
                f"{decision['action']}."
            )
        )

        return " ".join(parts)

    # ==============================================================
    # Service Failure
    # ==============================================================

    def _service_failure_response(
        self,
        request: TransactionRequest,
        tool_results: list,
        error: str,
    ) -> RiskManagerResponse:
        """
        Fail safely if the ML service is unavailable.

        We do NOT automatically approve a transaction when
        the primary risk model is unavailable.
        """

        decision = RiskDecision(
            risk_level="HIGH",
            action="MANUAL_REVIEW",
            confidence=None,
            reason=(
                "The ML risk prediction service was "
                "unavailable. The transaction requires "
                "manual review."
            ),
        )

        evidence = RiskEvidence(
            ml_risk_score=None,
            anomaly_detected=False,
            velocity_risk=None,
            customer_risk=None,
            transaction_risk=None,
            triggered_rules=[
                "ML_SERVICE_UNAVAILABLE"
            ],
        )

        return RiskManagerResponse(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            success=False,
            decision=decision,
            evidence=evidence,
            tool_results=tool_results,
            explanation=(
                "The transaction could not be fully "
                "evaluated because the ML prediction "
                "service was unavailable. Manual review "
                "is required."
            ),
            metadata={
                "error": error,
            },
        )