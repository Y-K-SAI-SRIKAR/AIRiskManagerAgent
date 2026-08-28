from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class TransactionRequest(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True
    )

    transaction_id: str = Field(
        ...,
        description="Unique identifier of the transaction"
    )

    customer_id: str = Field(
        ...,
        description="Unique identifier of the customer"
    )

    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount"
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="Transaction currency"
    )

    merchant_id: Optional[str] = Field(
        default=None,
        description="Merchant identifier"
    )

    merchant_category: Optional[str] = Field(
        default=None,
        description="Merchant category"
    )

    transaction_type: Optional[str] = Field(
        default=None,
        description="Transaction type such as purchase, transfer, withdrawal"
    )

    timestamp: datetime = Field(
        ...,
        description="Timestamp at which the transaction occurred"
    )

    device_id: Optional[str] = Field(
        default=None,
        description="Device associated with the transaction"
    )

    ip_address: Optional[str] = Field(
        default=None,
        description="IP address associated with the transaction"
    )

    location: Optional[str] = Field(
        default=None,
        description="Transaction location"
    )

    country: Optional[str] = Field(
        default=None,
        description="Transaction country"
    )

    channel: Optional[str] = Field(
        default=None,
        description="Transaction channel such as web, mobile, ATM, POS"
    )

    features: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional ML features required by the trained "
            "risk model"
        )
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional contextual information"
    )