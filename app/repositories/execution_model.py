from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Execution(Base):

    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    execution_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    execution_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    customer_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    job_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    tool_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    successful_tools: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    failed_tools: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    ml_model: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    ml_alias: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    ml_version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    ml_probability: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    ml_threshold: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    risk_level: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )

    action: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    total_transactions: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    fraud_transactions: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    legitimate_transactions: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    fraud_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    average_fraud_probability: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    result_s3_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    report_s3_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    triggered_rules: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )