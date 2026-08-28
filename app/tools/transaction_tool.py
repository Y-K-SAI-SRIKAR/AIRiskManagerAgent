from typing import Any, Dict, Optional

from app.repositories.transaction_repository import (
    TransactionRepository,
)


class TransactionToolError(Exception):
    """
    Raised when transaction analysis fails.
    """


class TransactionTool:
    """
    Tool used by the Agent to inspect transaction information.
    """

    def __init__(
        self,
        repository: TransactionRepository,
    ):
        self.repository = repository

    def get_transaction(
        self,
        transaction_id: str,
    ) -> Dict[str, Any]:

        transaction = self.repository.get_transaction(
            transaction_id
        )

        if transaction is None:
            raise TransactionToolError(
                f"Transaction '{transaction_id}' not found."
            )

        return transaction

    def analyze_transaction(
        self,
        transaction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract useful transaction-level risk signals.
        """

        amount = float(
            transaction.get("amount", 0)
        )

        result = {
            "transaction_id": transaction.get(
                "transaction_id"
            ),
            "customer_id": transaction.get(
                "customer_id"
            ),
            "amount": amount,
            "currency": transaction.get(
                "currency",
                "INR",
            ),
            "merchant_id": transaction.get(
                "merchant_id"
            ),
            "merchant_category": transaction.get(
                "merchant_category"
            ),
            "transaction_type": transaction.get(
                "transaction_type"
            ),
            "channel": transaction.get(
                "channel"
            ),
            "location": transaction.get(
                "location"
            ),
        }

        # Basic transaction-level indicators.
        result["high_amount"] = amount >= 50000

        result["has_device_id"] = bool(
            transaction.get("device_id")
        )

        result["has_location"] = bool(
            transaction.get("location")
        )

        return result