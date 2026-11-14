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

## Route a synthetic ticket

Set `OPENAI_API_KEY` and `ROUTER_MODEL` to a model that supports Chat Completions structured outputs. Send `POST /route` with an `Idempotency-Key` header and a JSON body such as:

```json
{"ticket_id":"ticket-1","text":"I was charged twice for the same purchase."}
```

The endpoint saves and returns a decision in shadow mode. Configure `ROUTER_DB_PATH` to use a persistent local SQLite file. The default is `routing.sqlite3` in the working directory. See the [agent contract](docs/agent-contract.md) and [evaluation plan](docs/evaluation-plan.md). When editing the routing policy, update the packaged copy and bump the policy version.
