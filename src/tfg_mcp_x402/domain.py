"""Deterministic local domain used by the HTTP gateway."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentProof:
    resource: str
    amount: int
    payer_id: str
    nonce: str
    expires_at: int


class LocalStore:
    """Minimal SQLite state for synthetic challenges and consumed nonces."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS consumed_nonces "
            "(nonce TEXT PRIMARY KEY, resource TEXT NOT NULL)"
        )
        self.connection.commit()

    def consume_nonce(self, proof: PaymentProof) -> bool:
        try:
            self.connection.execute(
                "INSERT INTO consumed_nonces (nonce, resource) VALUES (?, ?)",
                (proof.nonce, proof.resource),
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            return False
        return True


class VerificationError(ValueError):
    """Raised when synthetic payment proof validation fails."""


class SyntheticFacilitator:
    """Fail-closed verifier; it never performs settlement or network I/O."""

    def __init__(self, store: LocalStore, *, expected_amount: int = 1) -> None:
        self.store = store
        self.expected_amount = expected_amount

    def verify(self, proof: PaymentProof, *, resource: str, now: int) -> None:
        if proof.resource != resource:
            raise VerificationError("resource_mismatch")
        if proof.amount != self.expected_amount:
            raise VerificationError("amount_mismatch")
        if not proof.payer_id.startswith("lab-"):
            raise VerificationError("invalid_lab_payer")
        if proof.expires_at < now:
            raise VerificationError("expired_proof")
        if not self.store.consume_nonce(proof):
            raise VerificationError("nonce_reused")

