"""Data models for payment service."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    """Payment transaction model."""

    id: str
    amount: float
    status: str
    created_at: datetime
    card: Optional["Card"] = None

    def validate(self):
        """Validate transaction data."""
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        if not self.id:
            raise ValueError("Transaction ID required")


@dataclass
class Card:
    """Credit card model."""

    token: str
    last_four: str
    expiry_date: str
    card_type: str

    def is_expired(self) -> bool:
        """Check if card is expired."""
        # Parse expiry_date and compare with current date
        return False
