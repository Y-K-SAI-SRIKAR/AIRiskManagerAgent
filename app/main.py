import os
import tempfile
from pathlib import Path
import json

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.agent import RiskManagerAgent
from app.database import SessionLocal
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.request import TransactionRequest
from app.schemas.response import RiskManagerResponse
from app.tools.batch_prediction_tool import BatchPredictionTool
from app.repositories.execution_model import Execution


app = FastAPI(
    title="AI Risk Manager Agent",
    description=(
        "Agentic transaction risk analysis API powered by "
        "deterministic risk tools and a deployed ML model."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# Agent
# ---------------------------------------------------------

agent = RiskManagerAgent()


# ---------------------------------------------------------
# Batch Prediction Tool
# ---------------------------------------------------------

batch_prediction_tool = BatchPredictionTool()


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get(
    "/health",
    tags=["Health"],
)
async def health():
    """
    Health check for the Agent service.
    """

    return {
        "status": "healthy",
        "service": "AI Risk Manager Agent",
    }


def serialize_execution(
    execution: Execution,
) -> dict:
    """
    Convert an Execution database record into
    a frontend-friendly JSON response.
    """

    triggered_rules = []

    if execution.triggered_rules:

        try:
            triggered_rules = json.loads(
                execution.triggered_rules
            )

        except (json.JSONDecodeError, TypeError):

            triggered_rules = [
                execution.triggered_rules
            ]

    return {
        "id": execution.id,
        "execution_id": execution.execution_id,
        "execution_type": execution.execution_type,

        "transaction_id": execution.transaction_id,
        "customer_id": execution.customer_id,
        "job_id": execution.job_id,

        "status": execution.status,

        "started_at": (
            execution.started_at.isoformat()
            if execution.started_at
            else None
        ),

        "completed_at": (
            execution.completed_at.isoformat()
            if execution.completed_at
            else None
        ),

        "tools": {
            "total": execution.tool_count,
            "successful": execution.successful_tools,
            "failed": execution.failed_tools,
        },

        "ml": {
            "model": execution.ml_model,
            "alias": execution.ml_alias,
            "version": execution.ml_version,
            "probability": execution.ml_probability,
            "threshold": execution.ml_threshold,
        },

        "decision": {
            "risk_level": execution.risk_level,
            "action": execution.action,
            "triggered_rules": triggered_rules,
        },

        "batch": {
            "total_transactions": execution.total_transactions,
            "fraud_transactions": execution.fraud_transactions,
            "legitimate_transactions": execution.legitimate_transactions,
            "fraud_rate": execution.fraud_rate,
            "average_fraud_probability": (
                execution.average_fraud_probability
            ),
        },

        "artifacts": {
            "result_s3_key": execution.result_s3_key,
            "report_s3_key": execution.report_s3_key,
        },

        "error": execution.error,
    }

# ---------------------------------------------------------
# Single Transaction Analysis
# ---------------------------------------------------------

@app.post(
    "/analyze",
    response_model=RiskManagerResponse,
    tags=["Risk Analysis"],
)
async def analyze_transaction(
    request: TransactionRequest,
):
    """
    Analyze a single transaction using the Agent.

    Execution metadata is persisted to the RDS database.
    """

    db = SessionLocal()

    execution = None

    try:

        # -------------------------------------------------
        # Create execution record
        # -------------------------------------------------

        repository = ExecutionRepository(db)

        execution = repository.create_execution(
            execution_type="SINGLE",
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
        )

        # -------------------------------------------------
        # Execute Agent
        # -------------------------------------------------

        result = await agent.analyze(request)

        # Convert Pydantic response to dictionary
        result_data = result.model_dump()

        repository.complete_execution(
            execution,
            result_data,
        )

        return result

    except Exception as exc:

        # -------------------------------------------------
        # Store failed execution
        # -------------------------------------------------

        if execution is not None:

            try:

                repository.fail_execution(
                    execution,
                    str(exc),
                )

            except Exception:
                # Do not hide the original exception if
                # database persistence itself fails.
                pass

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    finally:

        db.close()


# ---------------------------------------------------------
# Batch CSV Analysis
# ---------------------------------------------------------

@app.post(
    "/analyze/batch",
    tags=["Batch Risk Analysis"],
)
async def analyze_batch(
    file: UploadFile = File(...),
):
    """
    Analyze an uploaded CSV using the ML batch prediction
    service.

    The CSV itself is NOT stored in RDS.

    Execution metadata is stored in RDS while the ML service
    continues to manage prediction/report artifacts in S3.
    """

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="A CSV file must be provided.",
        )

    filename = Path(file.filename).name

    if not filename.lower().endswith(".csv"):

        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    temporary_path = None

    db = SessionLocal()

    execution = None

    repository = ExecutionRepository(db)

    try:

        # -------------------------------------------------
        # Create batch execution record
        # -------------------------------------------------

        execution = repository.create_execution(
            execution_type="BATCH",
        )

        # -------------------------------------------------
        # Create temporary CSV file
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".csv",
            delete=False,
        ) as temporary_file:

            temporary_path = temporary_file.name

            # Copy uploaded file to disk in chunks.
            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                temporary_file.write(chunk)

        # -------------------------------------------------
        # Send CSV to ML batch service
        # -------------------------------------------------

        result = await batch_prediction_tool.analyze_csv(
            file_path=temporary_path,
            filename=filename,
        )

        # -------------------------------------------------
        # Handle batch prediction failure
        # -------------------------------------------------

        if not result.get("success"):

            error_message = result.get(
                "error",
                "Batch prediction service failed.",
            )

            repository.fail_execution(
                execution,
                error_message,
            )

            raise HTTPException(
                status_code=502,
                detail=error_message,
            )

        # -------------------------------------------------
        # Extract ML response
        # -------------------------------------------------

        data = result.get(
            "data",
            {},
        )

        # -------------------------------------------------
        # Persist batch execution metadata
        # -------------------------------------------------

        repository.complete_batch_execution(
            execution,
            data,
        )

        # -------------------------------------------------
        # Return normalized Agent API response
        # -------------------------------------------------

        return {
            "success": True,

            "job_id": data.get(
                "job_id"
            ),

            "status": "completed",

            "summary": {
                "total_transactions": data.get(
                    "total_transactions"
                ),

                "fraud_transactions": data.get(
                    "fraud_transactions"
                ),

                "legitimate_transactions": data.get(
                    "legitimate_transactions"
                ),

                "fraud_rate": data.get(
                    "fraud_rate"
                ),

                "average_fraud_probability": data.get(
                    "average_fraud_probability"
                ),

                "production_threshold": data.get(
                    "production_threshold"
                ),
            },

            "model": {
                "name": data.get(
                    "model"
                ),

                "alias": data.get(
                    "alias"
                ),

                "version": data.get(
                    "model_version"
                ),

                "type": data.get(
                    "model_type"
                ),

                "xgb_weight": data.get(
                    "xgb_weight"
                ),

                "nn_weight": data.get(
                    "nn_weight"
                ),
            },

            "artifacts": {
                "result_download_url": data.get(
                    "result_download_url"
                ),

                "report_download_url": data.get(
                    "report_download_url"
                ),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:

        # -------------------------------------------------
        # Persist unexpected failure
        # -------------------------------------------------

        if execution is not None:

            try:

                repository.fail_execution(
                    execution,
                    str(exc),
                )

            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {exc}",
        ) from exc

    finally:

        # -------------------------------------------------
        # Remove temporary file
        # -------------------------------------------------

        if temporary_path:

            try:
                os.remove(
                    temporary_path
                )

            except OSError:
                pass

        # -------------------------------------------------
        # Close uploaded file
        # -------------------------------------------------

        await file.close()

        # -------------------------------------------------
        # Close database session
        # -------------------------------------------------

        db.close()

# ---------------------------------------------------------
# Execution History
# ---------------------------------------------------------

@app.get(
    "/executions",
    tags=["Execution History"],
)
async def get_executions(
    limit: int = 50,
    offset: int = 0,
):
    """
    Retrieve Agent execution history.
    """

    if limit < 1 or limit > 100:

        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    if offset < 0:

        raise HTTPException(
            status_code=400,
            detail="offset must be greater than or equal to 0.",
        )

    db = SessionLocal()

    try:

        repository = ExecutionRepository(db)

        executions = repository.get_executions(
            limit=limit,
            offset=offset,
        )

        total = repository.count_executions()

        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "executions": [
                serialize_execution(execution)
                for execution in executions
            ],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve executions: {exc}",
        ) from exc

    finally:

        db.close()


# ---------------------------------------------------------
# Execution By ID
# ---------------------------------------------------------

@app.get(
    "/executions/{execution_id}",
    tags=["Execution History"],
)
async def get_execution(
    execution_id: str,
):
    """
    Retrieve a specific Agent execution.
    """

    db = SessionLocal()

    try:

        repository = ExecutionRepository(db)

        execution = repository.get_by_execution_id(
            execution_id
        )

        if execution is None:

            raise HTTPException(
                status_code=404,
                detail="Execution not found.",
            )

        return {
            "success": True,
            "execution": serialize_execution(
                execution
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve execution: {exc}",
        ) from exc

    finally:

        db.close()


# ---------------------------------------------------------
# Execution By Batch Job ID
# ---------------------------------------------------------

@app.get(
    "/executions/job/{job_id}",
    tags=["Execution History"],
)
async def get_execution_by_job(
    job_id: str,
):
    """
    Retrieve a batch execution using its ML job ID.
    """

    db = SessionLocal()

    try:

        repository = ExecutionRepository(db)

        execution = repository.get_by_job_id(
            job_id
        )

        if execution is None:

            raise HTTPException(
                status_code=404,
                detail="Execution for the specified job was not found.",
            )

        return {
            "success": True,
            "execution": serialize_execution(
                execution
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve batch execution: {exc}",
        ) from exc

    finally:

        db.close()