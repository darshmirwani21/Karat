"""
Banking API endpoints for Plaid integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from banking.plaid_client import PlaidClient
from banking import service as banking_service
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class ConnectRequest(BaseModel):
    """Request body for connect"""
    public_token: str
    user_id: int = 1


class AccountResponse(BaseModel):
    """Account response model"""
    id: int
    name: str
    type: str
    balance: float
    currency: str = "USD"


class TransactionResponse(BaseModel):
    """Transaction response model"""
    id: int
    amount: float
    date: Optional[str]
    merchant_name: Optional[str]
    category: str
    description: Optional[str]


@router.get("/link_token")
async def create_link_token(user_id: int = Query(1, description="Current user id")):
    """
    Create a Plaid Link token for the frontend to initialize Plaid Link.
    """
    client = PlaidClient()
    if not client.is_configured():
        raise HTTPException(status_code=503, detail="Plaid is not configured")
    try:
        link_token = client.create_link_token(str(user_id))
        return {"link_token": link_token}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/connect")
async def connect_bank_account(
    body: ConnectRequest,
    db: Session = Depends(get_db),
):
    """
    Connect a bank account using Plaid Link public token.
    """
    try:
        result = banking_service.connect_bank(body.user_id, body.public_token, db)
        return {"status": "connected", "message": "Bank account connected successfully", **result}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts")
async def get_accounts(
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """
    Get all connected bank accounts for the given user.
    """
    accounts = banking_service.get_accounts_for_user(user_id, db)
    return {"accounts": accounts}


@router.post("/sync")
async def sync_transactions(
    account_id: int = Query(..., description="Account id to sync"),
    db: Session = Depends(get_db),
):
    """
    Sync transactions for a specific account from Plaid.
    """
    try:
        count = banking_service.sync_account_transactions(account_id, db)
        return {"status": "synced", "transactions_count": count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/transactions")
async def get_transactions(
    user_id: int = Query(1),
    account_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get transactions for the user with optional filters.
    """
    transactions = banking_service.get_transactions_for_user(
        user_id, db, account_id=account_id, start_date=start_date, end_date=end_date
    )
    return {"transactions": transactions}
