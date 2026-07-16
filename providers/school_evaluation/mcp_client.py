"""Minimal stateless streamable-HTTP MCP client for the schoolinfo remote server.

Contract source: /tmp/schoolinfo-mcp@d7c78a3 (MIT). This is an independent client
(no vendored schoolinfo code); it speaks JSON-RPC 2.0 to the documented remote
endpoint so the adapter can call find_school / get_evaluation_plan with the server's
own API key. Injectable transport keeps tests offline.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Callable

REMOTE_SCHOOL_MCP = "https://mcp.gomdori.app/school"


def _http_post(url: str, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 fixed https
        raw = resp.read().decode("utf-8", "replace")
    # Support both direct JSON and SSE framing.
    if "data:" in raw and not raw.strip().startswith("{"):
        raw = "".join(line[5:] for line in raw.splitlines() if line.startswith("data:"))
    return json.loads(raw)


class SchoolMcpClient:
    def __init__(self, url: str = REMOTE_SCHOOL_MCP, *, timeout: int = 60, transport: Callable[[str, dict, int], dict] | None = None):
        self.url = url
        self.timeout = timeout
        self._transport = transport or _http_post
        self._id = 0

    def _rpc(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        return self._transport(self.url, {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}, self.timeout)

    def list_tools(self) -> list[str]:
        d = self._rpc("tools/list", {})
        return [t["name"] for t in d.get("result", {}).get("tools", [])]

    def call_tool(self, name: str, arguments: dict) -> dict:
        """Return {'ok': bool, 'text': str, 'error': ...}."""
        d = self._rpc("tools/call", {"name": name, "arguments": arguments})
        if "error" in d:
            return {"ok": False, "error": d["error"], "text": ""}
        content = d.get("result", {}).get("content", [])
        text = "\n".join(p.get("text", "") for p in content if p.get("type") == "text")
        is_error = bool(d.get("result", {}).get("isError"))
        # Some servers surface upstream errors as ok content beginning with '오류'.
        if is_error or text.startswith("오류") or text.startswith("ERR"):
            return {"ok": False, "error": text, "text": text}
        return {"ok": True, "text": text}
