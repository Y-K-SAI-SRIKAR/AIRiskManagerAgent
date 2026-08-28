from datetime import datetime
from typing import Any, Dict

from app.repositories.transaction_repository import (
    TransactionRepository,
)


class VelocityTool:
    def __init__(
        self,
        repository: TransactionRepository,
    ):
        self.repository = repository

    def analyze_velocity(
        self,
        customer_id: str,
        timestamp: datetime,
    ) -> Dict[str, Any]:

        last_5_minutes = (
            self.repository.count_recent_transactions(
                customer_id=customer_id,
                timestamp=timestamp,
                minutes=5,
            )
        )

        last_60_minutes = (
            self.repository.count_recent_transactions(
                customer_id=customer_id,
                timestamp=timestamp,
                minutes=60,
            )
        )

        # These are initial operational rules.
        # We can calibrate them later using your dataset.
        if last_5_minutes >= 5:
            velocity_risk = 0.95

        elif last_5_minutes >= 3:
            velocity_risk = 0.75

        elif last_60_minutes >= 10:
            velocity_risk = 0.80

        elif last_60_minutes >= 5:
            velocity_risk = 0.55

        else:
            velocity_risk = 0.10

        return {
            "customer_id": customer_id,
            "transactions_last_5_minutes": last_5_minutes,
            "transactions_last_60_minutes": last_60_minutes,
            "velocity_risk": velocity_risk,
            "velocity_anomaly": velocity_risk >= 0.75,
        }