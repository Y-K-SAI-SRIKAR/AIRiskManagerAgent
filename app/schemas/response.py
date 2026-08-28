from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """
    Result returned by an individual Agent tool.
    """

    tool_name: str = Field(
        ...,
        description="Name of the tool that produced the result"
    )

    success: bool = Field(
        ...,
        description="Whether the tool executed successfully"
    )

    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool output"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if the tool failed"
    )


class RiskEvidence(BaseModel):
    """
    Evidence used by the decision engine to determine risk.
    """

    ml_risk_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Risk probability produced by the ML model"
    )

    anomaly_detected: bool = Field(
        default=False,
        description="Whether anomalous behaviour was detected"
    )

    velocity_risk: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Transaction velocity risk score"
    )

    customer_risk: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Customer behavioural risk score"
    )

    transaction_risk: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Transaction-level risk score"
    )

    triggered_rules: List[str] = Field(
        default_factory=list,
        description="Risk rules triggered during evaluation"
    )


class RiskDecision(BaseModel):
    """
    Final deterministic decision produced by the risk engine.
    """

    risk_level: str = Field(
        ...,
        description="Final risk classification"
    )

    action: str = Field(
        ...,
        description="Recommended action"
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Decision confidence"
    )

    reason: str = Field(
        ...,
        description="Reason for the decision"
    )


class RiskManagerResponse(BaseModel):
    """
    Final response returned by the AI Risk Manager Agent.
    """

    transaction_id: str = Field(
        ...,
        description="Transaction identifier"
    )

    customer_id: str = Field(
        ...,
        description="Customer identifier"
    )

    success: bool = Field(
        ...,
        description="Whether the complete risk analysis succeeded"
    )

    decision: RiskDecision

    evidence: RiskEvidence

    tool_results: List[ToolResult] = Field(
        default_factory=list,
        description="Results returned by Agent tools"
    )

    explanation: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of the decision"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata"
    )