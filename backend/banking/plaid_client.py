"""
Plaid API client for banking integration
"""

import os
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

# Plaid SDK - optional so app can run without Plaid configured
try:
    from plaid.api import plaid_api
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
    from plaid.model.transactions_sync_request_options import TransactionsSyncRequestOptions
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    PLAID_AVAILABLE = True
except ImportError:
    PLAID_AVAILABLE = False
    plaid_api = None
    LinkTokenCreateRequest = None
    LinkTokenCreateRequestUser = None
    Products = None
    CountryCode = None


def _get_config():
    env = (os.getenv("PLAID_ENVIRONMENT") or "sandbox").lower()
    # Plaid host: sandbox, development, production
    host_map = {
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com",
    }
    host = host_map.get(env, host_map["sandbox"])
    return Configuration(
        host=host,
        api_key={
            "clientId": os.getenv("PLAID_CLIENT_ID") or "",
            "secret": os.getenv("PLAID_SECRET") or "",
        },
    )


class PlaidClient:
    """Wrapper for Plaid API client."""

    def __init__(self):
        if not PLAID_AVAILABLE:
            self.client = None
            return
        api_client = ApiClient(_get_config())
        self.client = plaid_api.PlaidApi(api_client)

    def is_configured(self) -> bool:
        return (
            PLAID_AVAILABLE
            and self.client is not None
            and bool(os.getenv("PLAID_CLIENT_ID") and os.getenv("PLAID_SECRET"))
        )

    def create_link_token(self, user_id: str) -> str:
        """Create a link_token for Plaid Link (frontend)."""
        if not self.client or not LinkTokenCreateRequest:
            raise RuntimeError("Plaid SDK not available")
        user = LinkTokenCreateRequestUser(client_user_id=str(user_id))
        req = LinkTokenCreateRequest(
            user=user,
            client_name="Karat",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en",
        )
        resp = self.client.link_token_create(req)
        return resp.link_token

    def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        """
        Exchange a public token for an access token and item_id.
        Returns {"access_token": str, "item_id": str}.
        """
        if not self.client:
            raise RuntimeError("Plaid SDK not available")
        req = ItemPublicTokenExchangeRequest(public_token=public_token)
        resp = self.client.item_public_token_exchange(req)
        return {"access_token": resp.access_token, "item_id": resp.item_id}

    def get_accounts(self, access_token: str) -> list[dict[str, Any]]:
        """
        Retrieve account information and balances.
        Returns list of {"account_id", "name", "type", "subtype", "balances"}.
        """
        if not self.client:
            raise RuntimeError("Plaid SDK not available")
        req = AccountsBalanceGetRequest(access_token=access_token)
        resp = self.client.accounts_balance_get(req)
        out = []
        for acc in resp.accounts:
            bal = acc.balances
            out.append({
                "account_id": acc.account_id,
                "name": acc.name or "",
                "type": acc.type or "other",
                "subtype": getattr(acc, "subtype", None) or "",
                "balances": {
                    "available": getattr(bal, "available", None),
                    "current": getattr(bal, "current", None),
                },
            })
        return out

    def sync_transactions(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        account_ids: Optional[list[str]] = None,
    ) -> tuple[list[dict[str, Any]], str, bool]:
        """
        Sync transactions (cursor-based). Returns (transactions, next_cursor, has_more).
        """
        if not self.client:
            raise RuntimeError("Plaid SDK not available")
        options = TransactionsSyncRequestOptions(account_ids=account_ids) if account_ids else None
        req = TransactionsSyncRequest(access_token=access_token, cursor=cursor, options=options)
        resp = self.client.transactions_sync(req)
        added = getattr(resp, "added", []) or []
        modified = getattr(resp, "modified", []) or []
        transactions = [self._normalize_transaction(t) for t in added + modified]
        next_cursor = getattr(resp, "next_cursor", "") or ""
        has_more = getattr(resp, "has_more", False)
        return transactions, next_cursor, has_more

    def _normalize_transaction(self, t: Any) -> dict[str, Any]:
        """Convert Plaid transaction object to a simple dict."""
        amount = getattr(t, "amount", None) or 0
        # Plaid: positive = outflow (expense), negative = inflow
        if getattr(t, "amount", None) is not None and getattr(t, "transaction_type", None) == "credit":
            amount = -float(amount)
        else:
            amount = float(amount)
        return {
            "transaction_id": getattr(t, "transaction_id", "") or "",
            "account_id": getattr(t, "account_id", "") or "",
            "amount": amount,
            "date": getattr(t, "date", None) or getattr(t, "authorized_date", None),
            "name": getattr(t, "name", "") or getattr(t, "merchant_name", "") or "",
            "category": (getattr(t, "personal_finance_category", None) or {}).get("primary", "other") if hasattr(t, "personal_finance_category") else "other",
            "description": getattr(t, "original_description", None) or getattr(t, "name", "") or "",
            "pending": getattr(t, "pending", False) or False,
        }
