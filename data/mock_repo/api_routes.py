"""API routes for payment service."""

from fastapi import APIRouter, HTTPException

from .database import DatabaseManager
from .payment_processor import PaymentProcessor

router = APIRouter()
db = DatabaseManager(config={})
processor = PaymentProcessor(db)


@router.post("/process-payment")
async def process_payment(transaction_id: str, amount: float, user_id: str):
    """Process a payment transaction."""
    try:
        result = processor.process_payment(
            transaction_id=transaction_id, amount=amount, user_id=user_id
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/refund-transaction")
async def refund_transaction(transaction_id: str):
    """Refund a payment transaction."""
    try:
        result = processor.refund(transaction_id)
        return {"status": "refunded", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
