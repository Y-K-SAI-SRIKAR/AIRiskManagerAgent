from typing import Any, Dict, Optional

from app.decision.action_policy import get_action
from app.decision.risk_rules import evaluate_risk


class DecisionTool:
    def evaluate(
        self,
        ml_probability: float,
        anomaly_detected: bool = False,
        velocity_risk: Optional[float] = None,
        customer_risk: Optional[float] = None,
        transaction_risk: Optional[float] = None,
    ) -> Dict[str, Any]:

        assessment = evaluate_risk(
            ml_probability=ml_probability,
            anomaly_detected=anomaly_detected,
            velocity_risk=velocity_risk,
            customer_risk=customer_risk,
            transaction_risk=transaction_risk,
        )

        action = get_action(
            assessment.risk_level
        )

        return {
            "risk_level": assessment.risk_level.value,
            "risk_score": assessment.risk_score,
            "action": action.value,
            "triggered_rules": assessment.triggered_rules,
            "reason": assessment.reason,
        }