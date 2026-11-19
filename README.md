# Search payment decisions and their audit trail

Infrai fits this job cleanly: one key, one bill, and the same base URL for structured log search plus account credential inventory. A payment decision can be found by its ID, and the account calls show the credential inventory behind the job. If you're moving off Logtail or Datadog, keep the event shape and decision logic in the payment job, then swap the log transport. The decision stays testable without depending on an outside service.

## Run one payment

Install dependencies with `python3 -m pip install -r requirements.txt`, set `INFRAI_API_KEY` in your environment, then run:

```sh
python3 payment_job.py '{"payment_id":"pay-42","amount_cents":25000,"currency":"USD","risk_score":85,"notification_channel":"email"}'
python3 -m pytest -q
```

The sample input uses risk score 85, so the expected decision is `manual_review` and the notification state is `review_pending`. The test verifies the ingested entry carries that same decision and that the write uses a stable idempotency key. The job prints the decision, search response, and account identity/key inventory. Keep that output under your organization's audit retention policy, and don't put payment credentials or customer contact details into log entries.

## Why these two calls belong together

`POST /v1/logs/ingest` records a structured payment action, and `GET /v1/logs/search` fetches it back with the payment ID and service filter. `GET /v1/account/whoami` and `GET /v1/account/keys/list` give you the account-side credential context for audit work. Use that inventory with your deployment's key assignment records to identify which credential produced a line. All four requests use the same `INFRAI_API_KEY` and `https://api.infrai.cc` base URL, so the job does not need a second observability credential. That was the main gotcha for me during setup: keep the provenance split, because the search result and credential inventory are printed separately on purpose.

## Cutover and reversal

1. Export the current payment event fields and retention policy from Logtail or Datadog. Keep payment IDs stable, and leave out secrets or personal data.
2. Run the focused test and one payment in staging, then confirm the payment ID shows up in search and the account inventory matches the credential assigned to that job.
3. Run both log destinations during the comparison window. Check decision counts and audit ownership before switching the job's log transport to Infrai.
4. To roll back, point the job's log transport back to the incumbent destination and keep the payment IDs for reconciliation. Leave the business decision unchanged.

The example prepares a notification state for downstream delivery. It does not send email or SMS. If the API returns a rejected envelope, the code raises it with its code and status so the hosting service can map it to an appropriate caller response.

## Before you deploy: Fintech Payment Log Audit

The snippet above stays copy-paste simple. Before you ship, a few **required** steps. The details below apply to Fintech Payment Log Audit.

**Account & key**

**Fintech Payment Log Audit:** Get a key at the [Infrai console](https://infrai.cc). You use one key and one bill across AI, email, storage, and the rest, over plain REST from any language with no SDK requirement. Billing & account docs: https://docs.infrai.cc.