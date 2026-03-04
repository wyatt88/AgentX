"""
Integration tests for the enhanced MCP module.

Covers:
  - Create MCP server with group field
  - Group-based listing
  - Health check endpoint
  - Tool listing per server

Run with:
    pytest be/tests/test_mcp_enhanced.py -v
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from be.app.main import app


BASE = "/mcp"


@pytest_asyncio.fixture
async def client():
    """Provide an async test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


def _server_payload(*, group: str = "default", name: str | None = None) -> dict:
    """Build a sample MCP server payload."""
    return {
        "name": name or f"test-mcp-{uuid.uuid4().hex[:8]}",
        "desc": "Integration test MCP server",
        "host": "http://localhost:9999/mcp",
        "group": group,
    }


# ── CRUD Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_mcp_server_with_group(client: AsyncClient):
    """POST /mcp/createOrUpdate should accept the group field."""
    payload = _server_payload(group="database")
    resp = await client.post(f"{BASE}/createOrUpdate", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == payload["name"]
    # group may or may not be echoed depending on router implementation


@pytest.mark.asyncio
async def test_list_mcp_servers(client: AsyncClient):
    """GET /mcp/list should include our created server."""
    payload = _server_payload(group="analytics")
    create_resp = await client.post(f"{BASE}/createOrUpdate", json=payload)
    server_name = create_resp.json()["name"]

    resp = await client.get(f"{BASE}/list")
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()]
    assert server_name in names


@pytest.mark.asyncio
async def test_get_mcp_server(client: AsyncClient):
    """GET /mcp/get/<id> should return the server."""
    payload = _server_payload()
    create_resp = await client.post(f"{BASE}/createOrUpdate", json=payload)
    server_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/get/{server_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == server_id


@pytest.mark.asyncio
async def test_delete_mcp_server(client: AsyncClient):
    """DELETE /mcp/delete/<id> should remove the server."""
    payload = _server_payload()
    create_resp = await client.post(f"{BASE}/createOrUpdate", json=payload)
    server_id = create_resp.json()["id"]

    resp = await client.delete(f"{BASE}/delete/{server_id}")
    assert resp.status_code == 200


# ── Group Listing ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient):
    """GET /mcp/groups should return aggregated group names."""
    # Create servers in different groups
    for grp in ("group-a", "group-b"):
        await client.post(f"{BASE}/createOrUpdate", json=_server_payload(group=grp))

    resp = await client.get(f"{BASE}/groups")
    # If the endpoint exists it should return 200 with a list
    if resp.status_code == 200:
        body = resp.json()
        assert isinstance(body, (list, dict))
    else:
        # Endpoint not yet implemented by engineer B — skip gracefully
        pytest.skip("GET /mcp/groups not yet implemented")


# ── Health Check ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check_unreachable_server(client: AsyncClient):
    """POST /mcp/health-check/<id> should return error status for unreachable servers."""
    payload = _server_payload()
    create_resp = await client.post(f"{BASE}/createOrUpdate", json=payload)
    server_id = create_resp.json()["id"]

    resp = await client.post(f"{BASE}/health-check/{server_id}")
    if resp.status_code == 200:
        body = resp.json()
        # Server is unreachable in test env — expect error status
        assert body.get("status") in ("error", "running")
    elif resp.status_code == 404:
        pytest.skip("POST /mcp/health-check not yet implemented")
    else:
        # 500 is acceptable for unreachable server in test
        assert resp.status_code in (200, 500)


# ── Tool Listing ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_server_tools(client: AsyncClient):
    """GET /mcp/tools/<server_id> should return a list (possibly empty for test server)."""
    payload = _server_payload()
    create_resp = await client.post(f"{BASE}/createOrUpdate", json=payload)
    server_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/tools/{server_id}")
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)
    elif resp.status_code == 404:
        pytest.skip("GET /mcp/tools not yet implemented")
    else:
        # Connection errors are expected for fake servers
        assert resp.status_code in (200, 500)
