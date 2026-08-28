from enum import Enum

from .risk_levels import RiskLevel


class RiskAction(str, Enum):
    APPROVE = "APPROVE"
    STEP_UP_AUTHENTICATION = "STEP_UP_AUTHENTICATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BLOCK = "BLOCK"


RISK_ACTION_POLICY = {
    RiskLevel.LOW: RiskAction.APPROVE,
    RiskLevel.MEDIUM: RiskAction.STEP_UP_AUTHENTICATION,
    RiskLevel.HIGH: RiskAction.MANUAL_REVIEW,
    RiskLevel.CRITICAL: RiskAction.BLOCK,
}


def get_action(risk_level: RiskLevel) -> RiskAction:
    try:
        return RISK_ACTION_POLICY[risk_level]

    except KeyError as exc:
        raise ValueError(
            f"No action policy defined for risk level: "
            f"{risk_level}"
        ) from exc