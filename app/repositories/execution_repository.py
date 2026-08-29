import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.execution_model import Execution


class ExecutionRepository:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_execution(
        self,
        execution_type: str,
        transaction_id: str | None = None,
        customer_id: str | None = None,
    ) -> Execution:

        execution = Execution(
            execution_id=uuid.uuid4().hex,
            execution_type=execution_type,
            transaction_id=transaction_id,
            customer_id=customer_id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc).replace(
                tzinfo=None
            ),
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        return execution

    # ---------------------------------------------------------
    # Complete Single Execution
    # ---------------------------------------------------------

    def complete_execution(
        self,
        execution: Execution,
        result: dict[str, Any],
    ) -> Execution:

        execution.status = "COMPLETED"

        execution.completed_at = (
            datetime.now(timezone.utc).replace(
                tzinfo=None
            )
        )

        decision = result.get("decision", {})
        evidence = result.get("evidence", {})
        metadata = result.get("metadata", {})
        tool_results = result.get("tool_results", [])

        execution.tool_count = len(tool_results)

        execution.successful_tools = sum(
            1
            for tool in tool_results
            if tool.get("success") is True
        )

        execution.failed_tools = sum(
            1
            for tool in tool_results
            if tool.get("success") is False
        )

        execution.ml_probability = (
            evidence.get("ml_risk_score")
        )

        execution.ml_model = metadata.get(
            "ml_model"
        )

        execution.ml_alias = metadata.get(
            "ml_alias"
        )

        execution.ml_threshold = metadata.get(
            "ml_threshold"
        )

        execution.risk_level = decision.get(
            "risk_level"
        )

        execution.action = decision.get(
            "action"
        )

        triggered_rules = evidence.get(
            "triggered_rules",
            [],
        )

        execution.triggered_rules = json.dumps(
            triggered_rules
        )

        self.db.commit()
        self.db.refresh(execution)

        return execution

    # ---------------------------------------------------------
    # Complete Batch Execution
    # ---------------------------------------------------------

    def complete_batch_execution(
        self,
        execution: Execution,
        result: dict[str, Any],
    ) -> Execution:

        execution.status = "COMPLETED"

        execution.completed_at = (
            datetime.now(timezone.utc).replace(
                tzinfo=None
            )
        )

        execution.job_id = result.get(
            "job_id"
        )

        execution.total_transactions = result.get(
            "total_transactions"
        )

        execution.fraud_transactions = result.get(
            "fraud_transactions"
        )

        execution.legitimate_transactions = result.get(
            "legitimate_transactions"
        )

        execution.fraud_rate = result.get(
            "fraud_rate"
        )

        execution.average_fraud_probability = result.get(
            "average_fraud_probability"
        )

        execution.ml_model = result.get(
            "model"
        )

        execution.ml_alias = result.get(
            "alias"
        )

        execution.ml_version = result.get(
            "model_version"
        )

        execution.ml_threshold = result.get(
            "production_threshold"
        )

        # Permanent S3 object keys only.
        # Never persist presigned URLs here.

        execution.result_s3_key = result.get(
            "result_s3_key"
        )

        execution.report_s3_key = result.get(
            "report_s3_key"
        )

        self.db.commit()
        self.db.refresh(execution)

        return execution

    # ---------------------------------------------------------
    # Failed Execution
    # ---------------------------------------------------------

    def fail_execution(
        self,
        execution: Execution,
        error: str,
    ) -> Execution:

        execution.status = "FAILED"

        execution.completed_at = (
            datetime.now(timezone.utc).replace(
                tzinfo=None
            )
        )

        execution.error = error

        self.db.commit()
        self.db.refresh(execution)

        return execution

    # ---------------------------------------------------------
    # Get By Execution ID
    # ---------------------------------------------------------

    def get_by_execution_id(
        self,
        execution_id: str,
    ) -> Execution | None:

        return (
            self.db.query(Execution)
            .filter(
                Execution.execution_id == execution_id
            )
            .first()
        )

    # ---------------------------------------------------------
    # Get By Job ID
    # ---------------------------------------------------------

    def get_by_job_id(
        self,
        job_id: str,
    ) -> Execution | None:

        return (
            self.db.query(Execution)
            .filter(
                Execution.job_id == job_id
            )
            .first()
        )

    # ---------------------------------------------------------
    # Get Execution History
    # ---------------------------------------------------------

    def get_executions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Execution]:

        return (
            self.db.query(Execution)
            .order_by(
                Execution.id.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    # ---------------------------------------------------------
    # Count Executions
    # ---------------------------------------------------------

    def count_executions(self) -> int:

        return self.db.query(
            Execution
        ).count()