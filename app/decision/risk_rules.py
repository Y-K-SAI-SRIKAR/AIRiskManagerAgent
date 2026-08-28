from dataclasses import dataclass
from typing import List, Optional

from .risk_levels import RiskLevel


@dataclass(frozen=True)
class RiskAssessment:
    """
    Result of evaluating all available risk signals.
    """

    risk_level: RiskLevel
    triggered_rules: List[str]
    risk_score: float
    reason: str


# ------------------------------------------------------------------
# Model threshold
# ------------------------------------------------------------------

# This is the production threshold selected by the ML pipeline.
# It is NOT the same thing as the Agent's risk-level boundaries.
ML_PRODUCTION_THRESHOLD = 0.48


# ------------------------------------------------------------------
# Agent risk-level boundaries
# ------------------------------------------------------------------
#
# These boundaries classify the ML probability into operational
# risk levels. They can later be calibrated using historical data.
#

LOW_RISK_MAX = 0.20
MEDIUM_RISK_MAX = 0.48
HIGH_RISK_MAX = 0.75


def classify_ml_risk(probability: float) -> RiskLevel:
    """
    Convert the ML fraud probability into an Agent risk level.
    """

    probability = _validate_probability(probability)

    if probability < LOW_RISK_MAX:
        return RiskLevel.LOW

    if probability < MEDIUM_RISK_MAX:
        return RiskLevel.MEDIUM

    if probability < HIGH_RISK_MAX:
        return RiskLevel.HIGH

    return RiskLevel.CRITICAL


def evaluate_risk(
    ml_probability: float,
    anomaly_detected: bool = False,
    velocity_risk: Optional[float] = None,
    customer_risk: Optional[float] = None,
    transaction_risk: Optional[float] = None,
) -> RiskAssessment:
    """
    Evaluate the overall transaction risk using ML output and
    additional behavioural signals.

    The ML probability provides the primary risk signal.

    Additional tools can increase the final risk level, but they
    cannot arbitrarily reduce a high-confidence ML risk decision.
    """

    probability = _validate_probability(ml_probability)

    risk_level = classify_ml_risk(probability)

    triggered_rules: List[str] = []

    # --------------------------------------------------------------
    # ML rules
    # --------------------------------------------------------------

    if probability >= ML_PRODUCTION_THRESHOLD:
        triggered_rules.append(
            "ML_FRAUD_THRESHOLD_EXCEEDED"
        )

    if probability >= HIGH_RISK_MAX:
        triggered_rules.append(
            "ML_HIGH_RISK_PROBABILITY"
        )

    # --------------------------------------------------------------
    # Anomaly rule
    # --------------------------------------------------------------

    if anomaly_detected:
        triggered_rules.append(
            "TRANSACTION_ANOMALY_DETECTED"
        )

        risk_level = _increase_risk_level(risk_level)

    # --------------------------------------------------------------
    # Velocity rule
    # --------------------------------------------------------------

    if velocity_risk is not None:
        velocity_risk = _validate_probability(velocity_risk)

        if velocity_risk >= 0.80:
            triggered_rules.append(
                "HIGH_VELOCITY_RISK"
            )

            risk_level = _increase_risk_level(risk_level)

        elif velocity_risk >= 0.50:
            triggered_rules.append(
                "ELEVATED_VELOCITY_RISK"
            )

    # --------------------------------------------------------------
    # Customer behavioural risk
    # --------------------------------------------------------------

    if customer_risk is not None:
        customer_risk = _validate_probability(customer_risk)

        if customer_risk >= 0.80:
            triggered_rules.append(
                "HIGH_CUSTOMER_BEHAVIOURAL_RISK"
            )

            risk_level = _increase_risk_level(risk_level)

        elif customer_risk >= 0.50:
            triggered_rules.append(
                "ELEVATED_CUSTOMER_BEHAVIOURAL_RISK"
            )

    # --------------------------------------------------------------
    # Transaction risk
    # --------------------------------------------------------------

    if transaction_risk is not None:
        transaction_risk = _validate_probability(transaction_risk)

        if transaction_risk >= 0.80:
            triggered_rules.append(
                "HIGH_TRANSACTION_RISK"
            )

            risk_level = _increase_risk_level(risk_level)

        elif transaction_risk >= 0.50:
            triggered_rules.append(
                "ELEVATED_TRANSACTION_RISK"
            )

    # --------------------------------------------------------------
    # Build explanation
    # --------------------------------------------------------------

    reason = _build_reason(
        probability=probability,
        risk_level=risk_level,
        triggered_rules=triggered_rules,
    )

    return RiskAssessment(
        risk_level=risk_level,
        triggered_rules=triggered_rules,
        risk_score=probability,
        reason=reason,
    )


def _increase_risk_level(
    risk_level: RiskLevel,
) -> RiskLevel:
    """
    Increase risk by one level.

    LOW -> MEDIUM
    MEDIUM -> HIGH
    HIGH -> CRITICAL
    CRITICAL -> CRITICAL
    """

    progression = {
        RiskLevel.LOW: RiskLevel.MEDIUM,
        RiskLevel.MEDIUM: RiskLevel.HIGH,
        RiskLevel.HIGH: RiskLevel.CRITICAL,
        RiskLevel.CRITICAL: RiskLevel.CRITICAL,
    }

    return progression[risk_level]


def _validate_probability(value: float) -> float:
    """
    Validate that a risk score is between 0 and 1.
    """

    value = float(value)

    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"Risk probability must be between 0 and 1. "
            f"Received: {value}"
        )

    return value


def _build_reason(
    probability: float,
    risk_level: RiskLevel,
    triggered_rules: List[str],
) -> str:

    if not triggered_rules:
        return (
            f"ML fraud probability is {probability:.4f}. "
            f"No additional risk rules were triggered."
        )

    rules = ", ".join(triggered_rules)

    return (
        f"ML fraud probability is {probability:.4f}. "
        f"Final risk level is {risk_level.value}. "
        f"Triggered rules: {rules}."
    )