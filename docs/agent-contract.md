# Ticket routing agent contract

## Authority

The LLM selects a queue or human review by applying the full [routing policy](routing-rules.md). The harness supplies the policy as trusted instructions and treats ticket text as data. The model has no queue credentials or tools that modify tickets. In live mode the worker automatically delivers eligible decisions to their destination, including the review queue for human-review outcomes.

## Decision API

`POST /route` accepts a nonblank `ticket_id` and nonblank `text`. Supply an `Idempotency-Key` for each distinct routing attempt. The same key and payload return the saved decision, including a saved fallback. Reusing the key with different input returns HTTP 409. A concurrent duplicate whose decision is still pending returns HTTP 409 with a retryable error code. A deliberate reroute uses a new key. Invalid input returns HTTP 422.

HTTP 200 means the decision was saved. Delivery status is tracked separately.

```json
{
  "decision_id": "dec_123",
  "ticket_id": "ticket_123",
  "outcome": "billing",
  "policy_id": "BIL-01",
  "policy_version": "2026-11-14.1",
  "source": "model",
  "fallback_reason": null
}
```

- `outcome` is one of `returns`, `billing`, `account_access`, `technical_support`, or `human_review`.
- The model provides only `outcome` and `policy_id`. The harness checks the schema and verifies that the policy ID maps to the selected outcome in the exact policy version supplied to the model. Evaluation measures whether that valid pair correctly applies to the ticket.
- On a model timeout, provider failure, or invalid response, save `human_review` with `source: "fallback"`, `policy_id: null`, and a `fallback_reason` of `model_timeout`, `model_unavailable`, or `invalid_model_response`, respectively. A policy-based human-review decision keeps its review policy ID and `source: "model"`.
- If storage is unavailable, return HTTP 503. The client retries with the original key. The harness owns the policy version, decision ID, and fallback metadata.

## Dispatch and rollout

1. In shadow mode, save the decision for evaluation. In live mode, atomically save the decision and its dispatch job for enabled destinations. Send operational fallbacks to the review queue in live mode. For a disabled automatic queue, send the ticket to human review and record the original recommendation and the rollout override separately.
2. The worker delivers using a stable dispatch ID derived from the decision ID. Persist delivery status as `pending`, `delivered`, or `failed`. The destination deduplicates by dispatch ID, including when it accepted a delivery but its acknowledgment was lost.
3. Retry transient failures with backoff and the original dispatch ID. Leave exhausted or permanent failures visible for operator recovery. Delivery retries reuse the saved decision without calling the model.
4. Reviewers see the ticket, suggested destination if present, policy clause and version, and the reason for review. Keep raw ticket text out of telemetry. To suspend automatic routing, switch live delivery to review-only and apply that control to pending jobs before dispatch.

## Acceptance criteria

- A valid model decision is saved with its supporting policy ID and version.
- An unknown policy ID, an outcome-policy mismatch, and a timeout each produce a review fallback.
- A duplicate API request reuses the decision. A lost delivery acknowledgment still results in one queue entry.
- Shadow mode creates no dispatch job. Live mode delivers eligible decisions automatically and sends fallbacks and disabled-queue recommendations to review.
