import json

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


def valid_proof(
    nonce: str, resource: str = "/mcp/tools/echo/paid"
) -> dict[str, object]:
    return {
        "resource": resource,
        "amount": 1,
        "payer_id": "lab-client",
        "nonce": nonce,
        "expires_at": 2_000_000_000,
    }


def test_paid_echo_accepts_valid_synthetic_proof() -> None:
    response = client.post(
        "/mcp/tools/echo/paid",
        headers={"x-payment-proof": json.dumps(valid_proof("nonce-valid"))},
        json={"message": "hello"},
    )
    assert response.status_code == 200


def test_paid_echo_rejects_reused_nonce() -> None:
    headers = {"x-payment-proof": json.dumps(valid_proof("nonce-reused"))}
    first = client.post("/mcp/tools/echo/paid", headers=headers, json={"message": "hello"})
    second = client.post("/mcp/tools/echo/paid", headers=headers, json={"message": "hello"})
    assert first.status_code == 200
    assert second.status_code == 409


def test_mcp_lists_the_deterministic_tool() -> None:
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert response.status_code == 200
    assert response.json()["result"]["tools"][0]["name"] == "echo"


def test_paid_mcp_challenges_before_dispatch() -> None:
    response = client.post(
        "/mcp/paid",
        json={
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"message": "hello"}},
        },
    )
    assert response.status_code == 402


def test_paid_mcp_dispatches_after_synthetic_verification() -> None:
    response = client.post(
        "/mcp/paid",
        headers={
            "x-payment-proof": json.dumps(
                valid_proof("mcp-nonce", resource="/mcp/paid")
            )
        },
        json={
            "jsonrpc": "2.0",
            "id": "call-2",
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"message": "hello"}},
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["content"][0]["text"] == "hello"

