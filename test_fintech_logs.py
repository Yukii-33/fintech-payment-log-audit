from fintech_logs import PaymentEvent, decide, record_payment


def test_risky_payment_holds_receipt_and_records_the_same_decision(monkeypatch):
    observed = []
    monkeypatch.setattr("fintech_logs.call", lambda method, path, **kwargs:
                        observed.append((method, path, kwargs)))
    event = PaymentEvent(payment_id="pay-42", amount_cents=25000,
                         currency="USD", risk_score=85, notification_channel="email")

    assert decide(event)["notification"] == "review_pending"
    result = record_payment(event)

    assert result["action"] == "manual_review"
    assert observed[0][0:2] == ("POST", "/v1/logs/ingest")
    assert observed[0][2]["payload"]["entries"][0]["notification"] == "review_pending"
    assert observed[0][2]["payload"]["idempotency_key"] == "payment-decision:pay-42"
