from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Policy-Aware Ticket Router")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse()
