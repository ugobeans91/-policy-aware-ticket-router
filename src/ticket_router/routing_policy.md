# Support ticket routing rules

These synthetic policies select a queue. Routing does not approve a refund, return, or account change.

| Policy ID | Outcome | Applies when |
| --- | --- | --- |
| RET-01 | `returns` | The customer reports a damaged or wrong item or requests a return, replacement, or exchange. The ticket must include an order reference. A request to return an item for a refund belongs here. |
| BIL-01 | `billing` | The customer asks about an invoice, a posted charge, or the status of an already approved refund. An order reference is optional for intake. |
| ACC-01 | `account_access` | The customer cannot sign in, reset a password, unlock an account, or complete authentication. |
| TEC-01 | `technical_support` | The customer describes a software issue outside account access or billing, such as a crash, an error before payment is submitted, or a feature that fails to load. |
| REV-01 | `human_review` | The ticket contains multiple independently actionable issues that belong to different queues. |
| REV-02 | `human_review` | The ticket lacks enough information to identify an issue, or a returns request lacks the required order reference. |
| REV-03 | `human_review` | The ticket describes a clear issue outside the four supported queues. |

Apply REV-01 first. Treat details that explain a single issue as context. For example, an approved return explains why a customer is asking about a pending refund, so that ticket goes to Billing. After checking for multiple issues, apply REV-02 for missing routing information, then the matching queue rule or REV-03.
