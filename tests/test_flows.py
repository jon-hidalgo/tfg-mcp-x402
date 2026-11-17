from fastapi.testclient import TestClient

from tfg_mcp_x402.app import app


client = TestClient(app)


def test_health_declares_synthetic_only() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "payments": "synthetic-only"}


def test_baseline_echo_is_available_without_payment() -> None:
    response = client.post("/mcp/tools/echo", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json()["mode"] == "deterministic-local"


def test_paid_echo_challenges_without_proof() -> None:
    response = client.post("/mcp/tools/echo/paid", json={"message": "hello"})
    assert response.status_code == 402
    assert response.json()["detail"]["mode"] == "synthetic-local-only"


def valid_proof(nonce: str) -> dict[str, object]:
    return {
        "resource": "/mcp/tools/echo/paid",
        "amount": 1,
        "payer_id": "lab-client",
        "nonce": nonce,
        "expires_at": 2_000_000_000,
    }


def test_paid_echo_accepts_valid_synthetic_proof() -> None:
    response = client.post(
        "/mcp/tools/echo/paid",
        headers={"x-payment-proof": str(valid_proof("nonce-valid"))},
        json={"message": "hello"},
    )
    assert response.status_code == 200


def test_paid_echo_rejects_reused_nonce() -> None:
    headers = {"x-payment-proof": str(valid_proof("nonce-reused"))}
    first = client.post("/mcp/tools/echo/paid", headers=headers, json={"message": "hello"})
    second = client.post("/mcp/tools/echo/paid", headers=headers, json={"message": "hello"})
    assert first.status_code == 200
    assert second.status_code == 409

