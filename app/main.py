import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.agent import RiskManagerAgent
from app.schemas.request import TransactionRequest
from app.schemas.response import RiskManagerResponse
from app.tools.batch_prediction_tool import BatchPredictionTool


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

    try:
        result = await agent.analyze(request)

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


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

    try:
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

                chunk = await file.read(1024 * 1024)

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

            raise HTTPException(
                status_code=502,
                detail=result.get(
                    "error",
                    "Batch prediction service failed.",
                ),
            )

        # -------------------------------------------------
        # Extract ML response
        # -------------------------------------------------

        data = result.get("data", {})

        # -------------------------------------------------
        # Return normalized Agent API response
        # -------------------------------------------------

        return {
            "success": True,
            "job_id": data.get("job_id"),
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
                "name": data.get("model"),
                "alias": data.get("alias"),
                "version": data.get("model_version"),
                "type": data.get("model_type"),
                "xgb_weight": data.get("xgb_weight"),
                "nn_weight": data.get("nn_weight"),
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
                os.remove(temporary_path)

            except OSError:
                pass

        # Close uploaded file
        await file.close()