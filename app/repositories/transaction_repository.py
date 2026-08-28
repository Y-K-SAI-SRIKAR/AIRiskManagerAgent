from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class TransactionRepository:

    def __init__(
        self,
        transactions: Optional[List[Dict[str, Any]]] = None,
    ):
        self._transactions = transactions or []

    def add_transaction(
        self,
        transaction: Dict[str, Any],
    ) -> None:
        """
        Store a transaction.
        """

        self._transactions.append(transaction)

    def get_transaction(
        self,
        transaction_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a transaction by transaction ID.
        """

        for transaction in self._transactions:
            if transaction.get("transaction_id") == transaction_id:
                return transaction

        return None

    def get_customer_transactions(
        self,
        customer_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all transactions belonging to a customer.
        """

        return [
            transaction
            for transaction in self._transactions
            if transaction.get("customer_id") == customer_id
        ]

    def get_recent_customer_transactions(
        self,
        customer_id: str,
        timestamp: datetime,
        minutes: int,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customer transactions within a recent time window.
        """

        start_time = timestamp - timedelta(
            minutes=minutes
        )

        results = []

        for transaction in self.get_customer_transactions(
            customer_id
        ):
            transaction_timestamp = transaction.get(
                "timestamp"
            )

            if isinstance(transaction_timestamp, str):
                transaction_timestamp = datetime.fromisoformat(
                    transaction_timestamp
                )

            if not isinstance(
                transaction_timestamp,
                datetime,
            ):
                continue

            if (
                start_time
                <= transaction_timestamp
                <= timestamp
            ):
                results.append(transaction)

        return results

    def count_recent_transactions(
        self,
        customer_id: str,
        timestamp: datetime,
        minutes: int,
    ) -> int:
        """
        Count customer transactions in a time window.
        """

        return len(
            self.get_recent_customer_transactions(
                customer_id=customer_id,
                timestamp=timestamp,
                minutes=minutes,
            )
        )