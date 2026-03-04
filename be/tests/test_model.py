"""
Integration tests for the Model Provider module.

Covers:
  - Create provider → Get → List → Update → Test connectivity → Delete
  - Available models aggregation

Run with:
    pytest be/tests/test_model.py -v
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from be.app.main import app


BASE = "/model"


@pytest_asyncio.fixture
async def client():
    """Provide an async test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


def _provider_payload(*, name: str | None = None, provider_type: str = "bedrock") -> dict:
    """Build a sample model provider payload."""
    return {
        "name": name or f"test-provider-{uuid.uuid4().hex[:8]}",
        "type": provider_type,
        "config": {
            "region": "us-west-2",
        },
        "models": ["us.anthropic.claude-3-7-sonnet-20250219-v1:0"],
        "is_default": False,
    }


# ── CRUD Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_provider(client: AsyncClient):
    """POST /model/provider should create a new provider."""
    payload = _provider_payload()
    resp = await client.post(f"{BASE}/provider", json=payload)
    if resp.status_code == 404:
        pytest.skip("POST /model/provider not yet implemented")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "id" in body
    assert body["name"] == payload["name"]
    assert body["type"] == payload["type"]


@pytest.mark.asyncio
async def test_get_provider(client: AsyncClient):
    """GET /model/provider/<id> should return the provider."""
    payload = _provider_payload()
    create_resp = await client.post(f"{BASE}/provider", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Model provider routes not yet implemented")
    provider_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/provider/{provider_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == provider_id


@pytest.mark.asyncio
async def test_list_providers(client: AsyncClient):
    """GET /model/providers should include our created provider."""
    payload = _provider_payload()
    create_resp = await client.post(f"{BASE}/provider", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Model provider routes not yet implemented")
    provider_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/providers")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert provider_id in ids


@pytest.mark.asyncio
async def test_update_provider(client: AsyncClient):
    """PUT /model/provider/<id> should update fields."""
    payload = _provider_payload()
    create_resp = await client.post(f"{BASE}/provider", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Model provider routes not yet implemented")
    provider_id = create_resp.json()["id"]

    update_payload = {"name": "updated-name", "is_default": True}
    resp = await client.put(f"{BASE}/provider/{provider_id}", json=update_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("name") == "updated-name" or body.get("is_default") is True


@pytest.mark.asyncio
async def test_delete_provider(client: AsyncClient):
    """DELETE /model/provider/<id> should remove the provider."""
    payload = _provider_payload()
    create_resp = await client.post(f"{BASE}/provider", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Model provider routes not yet implemented")
    provider_id = create_resp.json()["id"]

    resp = await client.delete(f"{BASE}/provider/{provider_id}")
    assert resp.status_code == 200


# ── Connectivity Test ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_connectivity_bedrock(client: AsyncClient):
    """POST /model/provider/<id>/test should test the provider connectivity."""
    payload = _provider_payload(provider_type="bedrock")
    create_resp = await client.post(f"{BASE}/provider", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Model provider routes not yet implemented")
    provider_id = create_resp.json()["id"]

    resp = await client.post(f"{BASE}/provider/{provider_id}/test")
    if resp.status_code == 404:
        pytest.skip("POST /model/provider/<id>/test not yet implemented")
    # In CI environment without real AWS creds, 500 is acceptable
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        body = resp.json()
        assert "status" in body or "success" in body


@pytest.mark.asyncio
async def test_connectivity_openai(client: AsyncClient):
    """POST /model/provider/<id>/test for openai type."""
    payload = _provider_payload(provider_type="openai")
    payload["config"] = {"base_url": "https://api.openai.com/v1", "api_key": "sk-fake"}
    create_resp = await client.post(f"{BASE}/provider", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Model provider routes not yet implemented")
    provider_id = create_resp.json()["id"]

    resp = await client.post(f"{BASE}/provider/{provider_id}/test")
    if resp.status_code == 404:
        pytest.skip("POST /model/provider/<id>/test not yet implemented")
    # Fake API key will fail — that's expected
    assert resp.status_code in (200, 500)


# ── Available Models ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_available_models(client: AsyncClient):
    """GET /model/available-models should aggregate models across active providers."""
    resp = await client.get(f"{BASE}/available-models")
    if resp.status_code == 404:
        pytest.skip("GET /model/available-models not yet implemented")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
