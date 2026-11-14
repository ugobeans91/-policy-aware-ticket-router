# Policy-Aware Ticket Router

Routes support tickets using policy evidence and flags ambiguous cases for human review.

## Run locally

Use Python 3.11 or newer.

```bash
python -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on macOS or Linux, or `.venv\Scripts\Activate.ps1` in PowerShell.

```bash
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
python -m uvicorn ticket_router.main:app --reload
```

Open http://127.0.0.1:8000/health to check the service.

## First milestone

Implement `POST /route` with deterministic rules for Returns, Billing, Account Access, and Technical Support. Send ambiguous or incomplete tickets to human review. Develop against 20 synthetic cases and reserve a separate held-out evaluation set for later comparisons.
