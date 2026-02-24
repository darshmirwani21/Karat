"""
Banking service: connect, sync, and query accounts/transactions using Plaid + DB.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database import models
from database.connection import get_db
from banking.plaid_client import PlaidClient

# Map Plaid category (string) to our enum
_CATEGORY_MAP = {
    "food_and_drink": models.TransactionCategory.FOOD_AND_DRINK,
    "general_merchandise": models.TransactionCategory.GENERAL_MERCHANDISE,
    "transportation": models.TransactionCategory.TRANSPORTATION,
    "gas_stations": models.TransactionCategory.GAS_STATIONS,
    "groceries": models.TransactionCategory.GROCERIES,
    "restaurants": models.TransactionCategory.RESTAURANTS,
    "entertainment": models.TransactionCategory.ENTERTAINMENT,
    "travel": models.TransactionCategory.TRAVEL,
    "utilities": models.TransactionCategory.UTILITIES,
    "rent": models.TransactionCategory.RENT,
    "income": models.TransactionCategory.INCOME,
    "transfer": models.TransactionCategory.TRANSFER,
}


def _to_category(s: Optional[str]) -> models.TransactionCategory:
    if not s:
        return models.TransactionCategory.OTHER
    key = (s or "").lower().replace(" ", "_").replace("-", "_")
    return _CATEGORY_MAP.get(key, models.TransactionCategory.OTHER)


def connect_bank(user_id: int, public_token: str, db: Session) -> dict:
    """
    Exchange public_token, create PlaidItem, fetch and store accounts.
    Returns {"item_id": int, "accounts": [{"id", "name", "type", "balance"}]}.
    """
    client = PlaidClient()
    if not client.is_configured():
        raise RuntimeError("Plaid is not configured (set PLAID_CLIENT_ID and PLAID_SECRET)")
    data = client.exchange_public_token(public_token)
    access_token = data["access_token"]
    plaid_item_id = data["item_id"]

    # Ensure user exists (for demo we may have no auth - create stub if missing)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(
            id=user_id,
            email=f"user{user_id}@karat.demo",
            hashed_password="",
            full_name=f"User {user_id}",
        )
        db.add(user)
        db.flush()

    item = models.PlaidItem(
        user_id=user_id,
        plaid_item_id=plaid_item_id,
        access_token=access_token,
    )
    db.add(item)
    db.flush()

    plaid_accounts = client.get_accounts(access_token)
    account_ids = []
    for pa in plaid_accounts:
        bal = pa.get("balances") or {}
        current = bal.get("current")
        available = bal.get("available")
        balance = float(available if available is not None else current or 0)
        acc = models.Account(
            user_id=user_id,
            item_id=item.id,
            plaid_account_id=pa["account_id"],
            name=pa.get("name") or "Account",
            type=pa.get("type") or "other",
            balance=balance,
        )
        db.add(acc)
        db.flush()
        account_ids.append({"id": acc.id, "name": acc.name, "type": acc.type, "balance": acc.balance})

    db.commit()
    return {"item_id": item.id, "accounts": account_ids}


def sync_account_transactions(account_id: int, db: Session) -> int:
    """
    Sync transactions for one account. Uses item's access_token and cursor.
    Returns count of new/updated transactions.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or not account.item_id:
        raise ValueError("Account not found or not linked to Plaid")
    item = db.query(models.PlaidItem).filter(models.PlaidItem.id == account.item_id).first()
    if not item:
        raise ValueError("Plaid item not found")

    client = PlaidClient()
    if not client.is_configured():
        raise RuntimeError("Plaid is not configured")

    cursor = item.transactions_cursor
    total = 0
    while True:
        txns, next_cursor, has_more = client.sync_transactions(
            item.access_token,
            cursor=cursor,
            account_ids=[account.plaid_account_id],
        )
        for t in txns:
            tid = t.get("transaction_id")
            if not tid:
                continue
            existing = db.query(models.Transaction).filter(
                models.Transaction.plaid_transaction_id == tid
            ).first()
            date_val = t.get("date")
            if isinstance(date_val, str):
                date_val = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            amount = float(t.get("amount", 0))
            cat = _to_category(t.get("category"))
            if existing:
                total += 1
                existing.amount = amount
                existing.date = date_val
                existing.merchant_name = t.get("name") or t.get("description")
                existing.category = cat
                existing.description = t.get("description")
                existing.is_pending = t.get("pending", False)
            else:
                db.add(models.Transaction(
                    account_id=account_id,
                    plaid_transaction_id=tid,
                    amount=amount,
                    date=date_val,
                    merchant_name=t.get("name") or t.get("description"),
                    category=cat,
                    description=t.get("description"),
                    is_pending=t.get("pending", False),
                ))
                total += 1
        item.transactions_cursor = next_cursor
        if not has_more:
            break
        cursor = next_cursor

    # Record last successful sync time
    account.last_synced = datetime.utcnow()
    db.commit()
    return total


def get_accounts_for_user(user_id: int, db: Session) -> list:
    """Return list of account dicts for user."""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == user_id,
        models.Account.is_active == True,
    ).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "type": a.type,
            "balance": a.balance,
            "currency": a.currency or "USD",
        }
        for a in accounts
    ]


def get_transactions_for_user(
    user_id: int,
    db: Session,
    account_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list:
    """Return list of transaction dicts for user, optionally filtered."""
    q = (
        db.query(models.Transaction)
        .join(models.Account)
        .filter(models.Account.user_id == user_id)
    )
    if account_id is not None:
        q = q.filter(models.Transaction.account_id == account_id)
    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)
    rows = q.order_by(models.Transaction.date.desc()).limit(500).all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            # Transaction.date is non-nullable by schema; always return ISO string
            "date": t.date.isoformat(),
            "merchant_name": t.merchant_name,
            "category": t.category.value if t.category else "other",
            "description": t.description,
        }
        for t in rows
    ]
