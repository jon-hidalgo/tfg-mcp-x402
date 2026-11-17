"""Minimal deterministic MCP JSON-RPC boundary for the prototype."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


def rpc_error(request_id: int | str | None, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def dispatch(request: JsonRpcRequest) -> dict[str, Any]:
    if request.jsonrpc != "2.0":
        return rpc_error(request.id, -32600, "Invalid Request")

    if request.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Deterministic local echo tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"message": {"type": "string"}},
                            "required": ["message"],
                        },
                    }
                ]
            },
        }

    if request.method != "tools/call":
        return rpc_error(request.id, -32601, "Method not found")

    if request.params.get("name") != "echo":
        return rpc_error(request.id, -32602, "Unknown tool")

    arguments = request.params.get("arguments")
    if not isinstance(arguments, dict) or not isinstance(arguments.get("message"), str):
        return rpc_error(request.id, -32602, "Invalid tool arguments")

    message = arguments["message"]
    if not 1 <= len(message) <= 200:
        return rpc_error(request.id, -32602, "Invalid tool arguments")

    return {
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "content": [{"type": "text", "text": message}],
            "isError": False,
        },
    }

