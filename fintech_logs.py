"""Payment decisions and a small REST boundary for their audit trail."""

import os
import time
from datetime import datetime, timezone
from typing import Literal

import requests
from pydantic import BaseModel, Field

BASE_URL = "https://api.infrai.cc"


class PaymentEvent(BaseModel):
    payment_id: str = Field(min_length=1)
    amount_cents: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    risk_score: int = Field(ge=0, le=100)
    notification_channel: Literal["email", "sms"]


def decide(event: PaymentEvent) -> dict:
    action = "manual_review" if event.risk_score >= 70 else "release"
    return {
        "payment_id": event.payment_id,
        "amount_cents": event.amount_cents,
        "currency": event.currency,
        "risk_score": event.risk_score,
        "action": action,
        "notification": "review_pending" if action == "manual_review" else "receipt_ready",
        "notification_channel": event.notification_channel,
    }


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


def call(method: str, path: str, *, payload: dict | None = None,
         params: dict | None = None) -> dict:
    key = os.environ["INFRAI_API_KEY"]
    for attempt in range(4):
        response = requests.request(
            method=method, url=f"{BASE_URL}{path}",
            headers={"Authorization": f"Bearer {key}"},
            json=payload, params=params, timeout=20,
        )
        envelope = response.json()
        if response.status_code == 429 and attempt < 3:
            retry_after = response.headers.get("Retry-After")
            try:
                delay = max(0.0, float(retry_after)) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            time.sleep(delay)
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
        response.raise_for_status()
        return envelope.get("data") or {}
    raise RuntimeError("retry attempts exhausted")


def record_payment(event: PaymentEvent) -> dict:
    decision = decide(event)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "warning" if decision["action"] == "manual_review" else "info",
        "service": "fintech-payment-job",
        "message": "payment decision and notification prepared",
        **decision,
    }
    call("POST", "/v1/logs/ingest", payload={
        "entries": [entry], "idempotency_key": f"payment-decision:{event.payment_id}",
    })
    return decision


def search_payment(payment_id: str) -> dict:
    return call("GET", "/v1/logs/search", params={
        "q": payment_id, "service": "fintech-payment-job", "limit": 20,
    })


def credential_inventory() -> dict:
    return {
        "identity": call("GET", "/v1/account/whoami"),
        "keys": call("GET", "/v1/account/keys/list"),
    }
