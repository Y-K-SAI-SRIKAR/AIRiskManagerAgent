from typing import Any, Dict

from app.repositories.transaction_repository import (
    TransactionRepository,
)


class CustomerHistoryTool:
    def __init__(
        self,
        repository: TransactionRepository,
    ):
        self.repository = repository

    def analyze_customer(
        self,
        customer_id: str,
        current_amount: float,
    ) -> Dict[str, Any]:

        transactions = (
            self.repository.get_customer_transactions(
                customer_id
            )
        )

        if not transactions:
            return {
                "customer_id": customer_id,
                "transaction_count": 0,
                "average_amount": 0.0,
                "maximum_amount": 0.0,
                "current_amount": current_amount,
                "customer_risk": 0.5,
                "history_available": False,
            }

        amounts = [
            float(transaction.get("amount", 0))
            for transaction in transactions
        ]

        average_amount = sum(amounts) / len(amounts)
        maximum_amount = max(amounts)

        # Compare current transaction with historical behaviour.
        if average_amount > 0:
            amount_ratio = (
                current_amount / average_amount
            )
        else:
            amount_ratio = 1.0

        if amount_ratio >= 10:
            customer_risk = 0.90

        elif amount_ratio >= 5:
            customer_risk = 0.75

        elif amount_ratio >= 3:
            customer_risk = 0.60

        else:
            customer_risk = 0.20

        return {
            "customer_id": customer_id,
            "transaction_count": len(transactions),
            "average_amount": round(
                average_amount,
                2,
            ),
            "maximum_amount": round(
                maximum_amount,
                2,
            ),
            "current_amount": current_amount,
            "amount_ratio": round(
                amount_ratio,
                2,
            ),
            "customer_risk": customer_risk,
            "history_available": True,
        }