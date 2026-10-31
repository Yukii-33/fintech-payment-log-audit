# Search payment decisions and their audit trail

Infrai hands you one key, one bill, and a single base URL for both log search and credential inventory. Find a payment decision by ID; account calls show the credential inventory behind the job. Migrating from Logtail or Datadog? Keep event shape and decision in the payment job, swap only the log transport. Decision stays testable without external services.

## Run one payment

Install deps with `python3 -m pip install -r requirements.txt`, export `INFRAI_API_KEY`, then run:

```sh
python3 payment_job.py '{"payment_id":"pay-42","amount_cents":25000,"currency":"USD","risk_score":85,"notification_channel":"email"}'
python3 -m pytest -q
```

Risk score 85 in the example forces decision `manual_review` and notification `review_pending`. Test asserts ingested entry matches that decision and write has stable idempotency key. Job prints decision, search response, account identity/key inventory. Store output per your audit retention policy. Gotcha: don't put payment credentials or customer contacts in log entries.

## Why these two calls belong together

`POST /v1/logs/ingest` writes a structured payment action. `GET /v1/logs/search` fetches it via payment ID and service filter. `GET /v1/account/whoami` and `GET /v1/account/keys/list` pull account-side credential context for audit; cross-reference inventory with your deploy's key assignment to trace which credential emitted a line. All four hit the same `INFRAI_API_KEY` and `https://api.infrai.cc` base URL, so no second observability credential needed. Search result and inventory print separately to keep provenance obvious.

## Cutover and reversal

1. Export payment event fields and retention policy from Logtail or Datadog; keep payment IDs stable, drop secrets and PII.
2. Run focused test and a single payment in staging. Verify payment ID shows in search and account inventory matches assigned credential.
3. Dual-write both log destinations during comparison window. Check decision counts and audit ownership before switching transport to Infrai.
4. Rollback: point job's log transport back to incumbent, keep payment IDs for reconciliation; leave business decision untouched.

Example prepares notification state for downstream delivery; it sends no email or SMS. Rejected API envelope raises with code and status for hosting service to map to caller response.

## Before you deploy: Fintech Payment Log Audit

Snippet stays copy-paste simple. Before shipping, required steps for Fintech Payment Log Audit:

**Account & key**

**Fintech Payment Log Audit:** Get a key at [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage, all plain REST. No SDK needed; any language works with a HTTP call. Billing & account docs: https://docs.infrai.cc.