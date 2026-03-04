"""
Integration tests for the Workflow module.

Covers the full lifecycle:
  Create → Get → Update → Execute → Execution History → Delete

Run with:
    pytest be/tests/test_workflow.py -v
"""

import json
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from be.app.main import app


BASE = "/workflow"


@pytest_asyncio.fixture
async def client():
    """Provide an async test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def sample_definition() -> dict:
    """Return a minimal valid workflow definition."""
    return {
        "nodes": [
            {
                "id": "start_1",
                "type": "start",
                "data": {"label": "Start"},
                "position": {"x": 0, "y": 0},
            },
            {
                "id": "agent_1",
                "type": "agent",
                "data": {"label": "Agent Node", "agent_id": "fake_agent_id"},
                "position": {"x": 200, "y": 0},
            },
            {
                "id": "end_1",
                "type": "end",
                "data": {"label": "End"},
                "position": {"x": 400, "y": 0},
            },
        ],
        "edges": [
            {"id": "e1", "source": "start_1", "target": "agent_1"},
            {"id": "e2", "source": "agent_1", "target": "end_1"},
        ],
    }


# ── CRUD Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient, sample_definition: dict):
    """POST /workflow/create should return the created workflow with an id."""
    payload = {
        "name": f"test-wf-{uuid.uuid4().hex[:8]}",
        "description": "Integration test workflow",
        "definition": json.dumps(sample_definition),
        "trigger_type": "manual",
    }
    resp = await client.post(f"{BASE}/create", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "id" in body
    assert body["name"] == payload["name"]
    assert body["status"] == "draft"


@pytest.mark.asyncio
async def test_get_workflow(client: AsyncClient, sample_definition: dict):
    """GET /workflow/get/<id> should return the previously created workflow."""
    # Create
    payload = {
        "name": f"test-get-{uuid.uuid4().hex[:8]}",
        "description": "Get test",
        "definition": json.dumps(sample_definition),
    }
    create_resp = await client.post(f"{BASE}/create", json=payload)
    wf_id = create_resp.json()["id"]

    # Get
    resp = await client.get(f"{BASE}/get/{wf_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == wf_id
    assert body["name"] == payload["name"]


@pytest.mark.asyncio
async def test_update_workflow(client: AsyncClient, sample_definition: dict):
    """PUT /workflow/update/<id> should modify the workflow."""
    # Create
    payload = {
        "name": f"test-upd-{uuid.uuid4().hex[:8]}",
        "description": "Before update",
        "definition": json.dumps(sample_definition),
    }
    create_resp = await client.post(f"{BASE}/create", json=payload)
    wf_id = create_resp.json()["id"]

    # Update
    update_payload = {"description": "After update", "status": "published"}
    resp = await client.put(f"{BASE}/update/{wf_id}", json=update_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "After update"
    assert body["status"] == "published"


@pytest.mark.asyncio
async def test_list_workflows(client: AsyncClient, sample_definition: dict):
    """GET /workflow/list should include the created workflow."""
    payload = {
        "name": f"test-list-{uuid.uuid4().hex[:8]}",
        "description": "List test",
        "definition": json.dumps(sample_definition),
    }
    create_resp = await client.post(f"{BASE}/create", json=payload)
    wf_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/list")
    assert resp.status_code == 200
    ids = [w["id"] for w in resp.json()]
    assert wf_id in ids


@pytest.mark.asyncio
async def test_delete_workflow(client: AsyncClient, sample_definition: dict):
    """DELETE /workflow/delete/<id> should remove the workflow."""
    payload = {
        "name": f"test-del-{uuid.uuid4().hex[:8]}",
        "description": "Delete test",
        "definition": json.dumps(sample_definition),
    }
    create_resp = await client.post(f"{BASE}/create", json=payload)
    wf_id = create_resp.json()["id"]

    resp = await client.delete(f"{BASE}/delete/{wf_id}")
    assert resp.status_code == 200

    # Verify gone — router returns 404 for non-existent workflows
    get_resp = await client.get(f"{BASE}/get/{wf_id}")
    assert get_resp.status_code == 404


# ── Execution Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_workflow_returns_sse(client: AsyncClient, sample_definition: dict):
    """POST /workflow/execute/<id> should return an SSE stream."""
    payload = {
        "name": f"test-exec-{uuid.uuid4().hex[:8]}",
        "description": "Execution test",
        "definition": json.dumps(sample_definition),
        "status": "published",
    }
    create_resp = await client.post(f"{BASE}/create", json=payload)
    wf_id = create_resp.json()["id"]

    resp = await client.post(
        f"{BASE}/execute/{wf_id}",
        json={"input": "Hello workflow"},
    )
    # SSE endpoint returns 200 with text/event-stream
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_execution_history(client: AsyncClient, sample_definition: dict):
    """GET /workflow/executions/<wf_id> should list execution records."""
    payload = {
        "name": f"test-hist-{uuid.uuid4().hex[:8]}",
        "description": "History test",
        "definition": json.dumps(sample_definition),
    }
    create_resp = await client.post(f"{BASE}/create", json=payload)
    wf_id = create_resp.json()["id"]

    # Trigger an execution (best-effort; engine may not fully run in test)
    await client.post(
        f"{BASE}/execute/{wf_id}",
        json={"input": "test"},
    )

    resp = await client.get(f"{BASE}/executions/{wf_id}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
