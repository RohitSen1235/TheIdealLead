from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from config import settings
from models import DBUser, DBTransaction

def calculate_amount_for_credits(credits: int) -> float:
    """Calculate the amount in USD for the requested number of credits"""
    return credits * settings.CREDIT_PRICE_USD

def create_payment_intent(db: Session, user: DBUser, credits: int) -> dict:
    """
    Development version: Automatically adds credits without payment processing
    """
    try:
        amount_usd = calculate_amount_for_credits(credits)
        
        # Create a new transaction record
        transaction = DBTransaction(
            user_id=user.id,
            amount=amount_usd,
            credits=credits,
            status='completed'  # Mark as completed immediately
        )
        db.add(transaction)
        
        # Add credits to user's account immediately
        user.credits += credits
        
        db.commit()

        return {
            'status': 'success',
            'amount': amount_usd,
            'credits': credits,
            'message': 'Credits added successfully'
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding credits: {str(e)}"
        )
