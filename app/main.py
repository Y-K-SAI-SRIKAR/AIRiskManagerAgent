from fastapi import FastAPI, HTTPException

from app.agent import RiskManagerAgent
from app.schemas.request import TransactionRequest
from app.schemas.response import RiskManagerResponse


app = FastAPI(
    title="AI Risk Manager Agent",
    description=(
        "Agentic transaction risk analysis API powered by "
        "deterministic risk tools and a deployed ML model."
    ),
    version="1.0.0",
)


agent = RiskManagerAgent()


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


@app.post(
    "/analyze",
    response_model=RiskManagerResponse,
    tags=["Risk Analysis"],
)
async def analyze_transaction(
    request: TransactionRequest,
):
    """
    Analyze a transaction using the Risk Manager Agent.
    """

    try:
        result = await agent.analyze(
            request
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc