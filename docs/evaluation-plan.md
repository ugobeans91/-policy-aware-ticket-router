# Routing evaluation plan

Use the 20 [development cases](../tests/fixtures/routing_cases.json) to tune the prompt and debug policy interpretation. Use the 28 [held-out cases](../evals/held_out.json) to screen a frozen candidate against the [routing policy](routing-rules.md). The held-out set contains four cases per policy clause, including refund context, payment-page failures, multiple actionable issues, missing information, and out-of-scope requests. The set is synthetic and balanced by design, so its coverage and error rates will differ from live traffic.

## Protocol

1. Review labels against the policy before scoring. Freeze the dataset commit, policy version, model identifier, generation settings, prompt, and harness version. Keep held-out ticket text and labels out of prompts, examples, tuning, and routine CI. The fixture is public, so treat it as a development-independent screen with possible exposure.
2. Run each ticket through the complete decision API in shadow mode using a fresh ticket ID and idempotency key. Give the model the ticket and full policy. Score the first response, including fallbacks, and report counts before rounding. Keep a per-case record of predicted and expected outcomes and policy IDs, source, fallback reason, and latency. A request with no saved decision is an execution failure and blocks advancement until investigated.
3. Use mocked provider responses in CI to verify malformed output, timeout, and policy mismatch behavior independently. If held-out failures inform a change, preserve those cases as regressions and freeze a fresh set for the next independent check.

## Metrics

| Metric | Definition |
| --- | --- |
| Automatic routing coverage | Predicted automatic queue divided by all tickets. In shadow mode this measures proposed automation. |
| Wrong-route rate | Predicted automatic queue that differs from the expected outcome divided by predicted automatic queues. This includes tickets that should have gone to human review. |
| Missed human-review rate | Expected human-review tickets assigned an automatic queue divided by expected human-review tickets. |
| Unnecessary review rate | Expected automatic-queue tickets sent to review divided by expected automatic-queue tickets. |
| Exact policy agreement | Tickets whose outcome and policy ID both match the label divided by all tickets. A fallback has no policy ID and fails this check. |
| Operational fallback rate | Harness-generated review fallbacks divided by all tickets. A policy-based review is separate. |

Report the confusion matrix, metrics by intended queue where applicable, and the raw numerator and denominator for every rate. Mark rates with zero denominator undefined.

## Proposed gates

These initial thresholds are for review before enabling automatic dispatch.

- **Synthetic screen to shadow pilot** — Zero wrong automatic routes, zero missed human-review cases, and at least 14 of the 16 automatic-eligible cases routed correctly. This allows up to two unnecessary reviews. Require at least 26 of 28 exact outcome-policy matches and zero operational fallbacks on the nominal run. Review all disagreements before advancing.
- **Shadow pilot to live dispatch** — For each proposed queue, collect independently labeled, representative shadow tickets. Require a one-sided 95% exact binomial upper confidence bound of at most 2% for wrong-route rate among tickets proposed for automatic dispatch to that queue. Require zero missed human-review cases across the adjudicated pilot and report its denominator. Require at least 80% of eligible tickets for each proposed queue to receive the correct automatic decision. Validate the adjudication and sampling design before interpreting intervals, particularly if tickets are correlated. Keep queues in shadow or human review until they qualify.
- With zero observed wrong routes, the 2% bound requires at least 149 independently labeled automatic decisions per proposed queue. A perfect score on the synthetic set supports starting a shadow pilot. Live dispatch requires separate evidence and agreement on these thresholds.
