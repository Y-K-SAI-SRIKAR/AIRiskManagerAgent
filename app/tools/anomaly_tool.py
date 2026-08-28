from typing import Any, Dict


class AnomalyTool:

    def analyze(
        self,
        transaction_analysis: Dict[str, Any],
        customer_history: Dict[str, Any],
        velocity: Dict[str, Any],
    ) -> Dict[str, Any]:

        triggered_anomalies = []

        # ----------------------------------------------------------
        # Amount anomaly
        # ----------------------------------------------------------

        amount_ratio = customer_history.get(
            "amount_ratio",
            1.0,
        )

        if amount_ratio >= 5:
            triggered_anomalies.append(
                "AMOUNT_SIGNIFICANTLY_ABOVE_CUSTOMER_BASELINE"
            )

        # ----------------------------------------------------------
        # Velocity anomaly
        # ----------------------------------------------------------

        if velocity.get("velocity_anomaly"):
            triggered_anomalies.append(
                "HIGH_TRANSACTION_VELOCITY"
            )

        # ----------------------------------------------------------
        # High-value transaction
        # ----------------------------------------------------------

        if transaction_analysis.get(
            "high_amount",
            False,
        ):
            triggered_anomalies.append(
                "HIGH_VALUE_TRANSACTION"
            )

        # ----------------------------------------------------------
        # New customer / no history
        # ----------------------------------------------------------

        if not customer_history.get(
            "history_available",
            False,
        ):
            triggered_anomalies.append(
                "NO_CUSTOMER_HISTORY_AVAILABLE"
            )

        anomaly_detected = bool(
            triggered_anomalies
        )

        if len(triggered_anomalies) >= 3:
            anomaly_score = 0.95

        elif len(triggered_anomalies) == 2:
            anomaly_score = 0.80

        elif len(triggered_anomalies) == 1:
            anomaly_score = 0.60

        else:
            anomaly_score = 0.10

        return {
            "anomaly_detected": anomaly_detected,
            "anomaly_score": anomaly_score,
            "triggered_anomalies": triggered_anomalies,
        }