"""FastAPI gateway and deterministic MCP-like tool endpoints."""

from __future__ import annotations

import sqlite3
import time
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from .domain import LocalStore, PaymentProof, SyntheticFacilitator, VerificationError

app = FastAPI(title="TFG MCP x402 local prototype", version="0.1.0")
store = LocalStore(sqlite3.connect(":memory:", check_same_thread=False))
facilitator = SyntheticFacilitator(store)
PAID_RESOURCE = "/mcp/tools/echo/paid"


class EchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=200)


class SyntheticPayment(BaseModel):
    resource: str
    amount: int = Field(ge=0)
    payer_id: str = Field(min_length=1, max_length=80)
    nonce: str = Field(min_length=1, max_length=120)
    expires_at: int


def echo_response(payload: EchoRequest) -> dict[str, str]:
    return {"message": payload.message, "mode": "deterministic-local"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "payments": "synthetic-only"}


@app.post("/mcp/tools/echo")
def baseline_echo(payload: EchoRequest) -> dict[str, str]:
    return echo_response(payload)


@app.post("/mcp/tools/echo/paid")
def paid_echo(
    payload: EchoRequest,
    request: Request,
    x_payment_proof: Annotated[SyntheticPayment | None, Header()] = None,
) -> dict[str, str]:
    if x_payment_proof is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "resource": PAID_RESOURCE,
                "amount": 1,
                "expires_in_seconds": 60,
                "mode": "synthetic-local-only",
            },
        )

    proof = PaymentProof(**x_payment_proof.model_dump())
    try:
        facilitator.verify(proof, resource=PAID_RESOURCE, now=int(time.time()))
    except VerificationError as error:
        code = 409 if str(error) == "nonce_reused" else 402
        raise HTTPException(status_code=code, detail=str(error)) from error

    return echo_response(payload)

