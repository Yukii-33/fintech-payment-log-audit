"""Run a payment decision, retrieve its log, and inspect credential ownership."""

import json
import sys

from fintech_logs import PaymentEvent, credential_inventory, record_payment, search_payment


def main() -> None:
    event = PaymentEvent.model_validate(json.loads(sys.argv[1]))
    print(json.dumps({
        "decision": record_payment(event),
        "search": search_payment(event.payment_id),
        "credential_inventory": credential_inventory(),
    }, indent=2))


if __name__ == "__main__":
    main()
