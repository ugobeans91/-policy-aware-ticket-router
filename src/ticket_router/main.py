import hashlib
import os
import sqlite3
import time
from contextlib import closing
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, StringConstraints

from ticket_router.routing import Decision, decide

app = FastAPI(title="Policy-Aware Ticket Router")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse()


Nonblank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CLAIM_SECONDS = 60


class RouteRequest(BaseModel):
    ticket_id: Nonblank
    text: Nonblank


@app.post("/route")
def route(
    ticket: RouteRequest,
    idempotency_key: Annotated[Nonblank, Header(alias="Idempotency-Key")],
) -> Decision:
    fingerprint = hashlib.sha256(ticket.model_dump_json().encode()).hexdigest()
    claim = uuid4().hex
    try:
        with closing(sqlite3.connect(os.getenv("ROUTER_DB_PATH", "routing.sqlite3"))) as db:
            with db:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS decisions (
                        key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                        claim TEXT NOT NULL, expires_at REAL NOT NULL, response TEXT
                    )
                """)
                db.execute("BEGIN IMMEDIATE")
                now = time.time()
                row = db.execute(
                    "SELECT fingerprint, expires_at, response FROM decisions WHERE key = ?",
                    (idempotency_key,),
                ).fetchone()
                if row:
                    saved_fingerprint, expires_at, response = row
                    if saved_fingerprint != fingerprint:
                        raise HTTPException(409, detail={"code": "idempotency_conflict"})
                    if response is not None:
                        return Decision.model_validate_json(response)
                    if expires_at > now:
                        raise HTTPException(409, detail={"code": "decision_pending"})
                    db.execute(
                        "UPDATE decisions SET claim = ?, expires_at = ? WHERE key = ?",
                        (claim, now + CLAIM_SECONDS, idempotency_key),
                    )
                else:
                    db.execute(
                        "INSERT INTO decisions VALUES (?, ?, ?, ?, NULL)",
                        (idempotency_key, fingerprint, claim, now + CLAIM_SECONDS),
                    )

            decision = decide(f"dec_{claim}", ticket.ticket_id, ticket.text)
            with db:
                update = db.execute(
                    "UPDATE decisions SET response = ? WHERE key = ? AND claim = ?",
                    (decision.model_dump_json(), idempotency_key, claim),
                )
                if update.rowcount != 1:
                    raise HTTPException(409, detail={"code": "decision_pending"})
            return decision
    except sqlite3.Error as exc:
        raise HTTPException(503, detail={"code": "storage_unavailable"}) from exc
