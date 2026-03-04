"""
Unit tests for the WorkflowEngine DAG traversal.

Tests:
  - 线性工作流: Start → Agent → End
  - 条件分支: Start → Condition → (true: Code, false: End)
  - 无 start 节点时的 fallback 行为
  - 条件节点路由边匹配

All DynamoDB calls and Agent calls are mocked.

Run with:
    pytest be/tests/test_engine.py -v
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from be.app.workflow.engine import WorkflowEngine
from be.app.workflow.models import WorkflowPO, WorkflowStatus


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_workflow(nodes: list, edges: list, **kwargs) -> WorkflowPO:
    """Build a WorkflowPO with a definition from nodes/edges."""
    definition = json.dumps({"nodes": nodes, "edges": edges})
    return WorkflowPO(
        id="wf-test-001",
        name="test-workflow",
        description="unit test",
        status=WorkflowStatus.published,
        definition=definition,
        **kwargs,
    )


def _mock_workflow_service():
    """Return a MagicMock that silences all WorkflowService DynamoDB calls."""
    svc = MagicMock()
    svc.add_execution = MagicMock()
    svc.update_execution = MagicMock()
    return svc


# ── Linear workflow: Start → Agent → End ─────────────────────────────────────


class TestLinearWorkflow:
    """线性工作流: Start → Agent → End"""

    @pytest.mark.asyncio
    async def test_linear_start_agent_end(self):
        """完整线性流程应产生 workflow_start, node events, workflow_complete"""
        nodes = [
            {"id": "s1", "type": "start", "config": {}},
            {"id": "a1", "type": "agent", "config": {"agent_id": "agent-001"}},
            {"id": "e1", "type": "end", "config": {}},
        ]
        edges = [
            {"id": "e1-edge", "source": "s1", "target": "a1"},
            {"id": "e2-edge", "source": "a1", "target": "e1"},
        ]
        wf = _make_workflow(nodes, edges)

        # Mock agent stream_chat — need to patch the executor's internal service
        async def mock_stream_chat(agent_id, user_message):
            yield {"data": "Agent says hi"}
            yield {"usage": {"totalTokens": 100}}

        # Get the registered AgentNodeExecutor singleton and replace its service
        from be.app.workflow.nodes import _EXECUTOR_REGISTRY
        agent_executor = _EXECUTOR_REGISTRY["agent"]
        original_service = agent_executor._agent_service

        mock_svc = MagicMock()
        mock_svc.stream_chat = mock_stream_chat
        agent_executor._agent_service = mock_svc

        try:
            with patch(
                "be.app.workflow.engine.WorkflowService",
                return_value=_mock_workflow_service(),
            ):
                engine = WorkflowEngine(wf)
                events = []
                async for sse in engine.execute({"query": "hello"}):
                    data = json.loads(sse.replace("data: ", "").strip())
                    events.append(data)
        finally:
            # Restore original service
            agent_executor._agent_service = original_service

        # Verify event sequence
        event_types = [e["event"] for e in events]
        assert event_types[0] == "workflow_start"
        assert "node_start" in event_types
        assert "node_complete" in event_types
        assert event_types[-1] == "workflow_complete"

        # Should have 3 node_start events (start, agent, end)
        node_starts = [e for e in events if e["event"] == "node_start"]
        assert len(node_starts) == 3

        # Workflow complete should have total_tokens from agent
        wf_complete = events[-1]
        assert wf_complete["total_tokens"] == 100


# ── Condition branch: Start → Condition → (true: Code, false: End) ───────────


class TestConditionBranchWorkflow:
    """条件分支工作流"""

    def _build_condition_workflow(self):
        nodes = [
            {"id": "s1", "type": "start", "config": {}},
            {
                "id": "c1",
                "type": "condition",
                "config": {
                    "expression": "context.get('input', {}).get('score', 0) > 60"
                },
            },
            {
                "id": "code1",
                "type": "code",
                "config": {"code": "result = 'PASS'"},
            },
            {"id": "e1", "type": "end", "config": {}},
        ]
        edges = [
            {"id": "edge1", "source": "s1", "target": "c1"},
            # true 分支 → code
            {"id": "edge2", "source": "c1", "target": "code1", "condition": "true"},
            # false 分支 → end
            {"id": "edge3", "source": "c1", "target": "e1", "condition": "false"},
            # code → end
            {"id": "edge4", "source": "code1", "target": "e1"},
        ]
        return _make_workflow(nodes, edges)

    @pytest.mark.asyncio
    async def test_condition_true_branch(self):
        """score > 60 → condition=true → Code 节点执行"""
        wf = self._build_condition_workflow()

        with patch(
            "be.app.workflow.engine.WorkflowService", return_value=_mock_workflow_service()
        ):
            engine = WorkflowEngine(wf)
            events = []
            async for sse in engine.execute({"score": 80}):
                data = json.loads(sse.replace("data: ", "").strip())
                events.append(data)

        event_types = [e["event"] for e in events]
        assert event_types[-1] == "workflow_complete"

        # Code 节点应被执行
        node_completes = [
            e for e in events if e["event"] == "node_complete"
        ]
        executed_nodes = [e["node_id"] for e in node_completes]
        assert "code1" in executed_nodes

        # Verify code output is PASS
        code_complete = next(e for e in node_completes if e["node_id"] == "code1")
        assert code_complete["output"] == "PASS"

    @pytest.mark.asyncio
    async def test_condition_false_branch(self):
        """score <= 60 → condition=false → 直接到 End 节点"""
        wf = self._build_condition_workflow()

        with patch(
            "be.app.workflow.engine.WorkflowService", return_value=_mock_workflow_service()
        ):
            engine = WorkflowEngine(wf)
            events = []
            async for sse in engine.execute({"score": 30}):
                data = json.loads(sse.replace("data: ", "").strip())
                events.append(data)

        event_types = [e["event"] for e in events]
        assert event_types[-1] == "workflow_complete"

        # Code 节点应 NOT 被执行（false 分支直接到 end）
        node_completes = [
            e for e in events if e["event"] == "node_complete"
        ]
        executed_nodes = [e["node_id"] for e in node_completes]
        assert "code1" not in executed_nodes
        assert "e1" in executed_nodes


# ── No start node fallback ───────────────────────────────────────────────────


class TestNoStartNodeFallback:
    """无 start 节点时应使用无入边的第一个节点"""

    @pytest.mark.asyncio
    async def test_fallback_to_no_incoming_node(self):
        """没有 start 类型节点时，引擎应找到无入边的节点作为起始"""
        nodes = [
            {
                "id": "code1",
                "type": "code",
                "config": {"code": "result = 'started from code'"},
            },
            {"id": "e1", "type": "end", "config": {}},
        ]
        edges = [
            {"id": "edge1", "source": "code1", "target": "e1"},
        ]
        wf = _make_workflow(nodes, edges)

        with patch(
            "be.app.workflow.engine.WorkflowService", return_value=_mock_workflow_service()
        ):
            engine = WorkflowEngine(wf)
            events = []
            async for sse in engine.execute({}):
                data = json.loads(sse.replace("data: ", "").strip())
                events.append(data)

        event_types = [e["event"] for e in events]
        assert event_types[0] == "workflow_start"
        assert event_types[-1] == "workflow_complete"

        # code1 should be the first executed node
        first_node_start = next(e for e in events if e["event"] == "node_start")
        assert first_node_start["node_id"] == "code1"

    @pytest.mark.asyncio
    async def test_no_nodes_raises_error(self):
        """空工作流应抛出错误"""
        wf = _make_workflow([], [])

        with patch(
            "be.app.workflow.engine.WorkflowService", return_value=_mock_workflow_service()
        ):
            engine = WorkflowEngine(wf)
            events = []
            async for sse in engine.execute({}):
                data = json.loads(sse.replace("data: ", "").strip())
                events.append(data)

        # Should end with workflow_error
        event_types = [e["event"] for e in events]
        assert "workflow_error" in event_types


# ── Edge routing ──────────────────────────────────────────────────────────────


class TestEdgeRouting:
    """测试边路由逻辑"""

    @pytest.mark.asyncio
    async def test_sourceHandle_condition_routing(self):
        """条件边使用 sourceHandle 字段也应正确路由"""
        nodes = [
            {"id": "s1", "type": "start", "config": {}},
            {
                "id": "c1",
                "type": "condition",
                "config": {"expression": "True"},
            },
            {
                "id": "code_t",
                "type": "code",
                "config": {"code": "result = 'TRUE_BRANCH'"},
            },
            {
                "id": "code_f",
                "type": "code",
                "config": {"code": "result = 'FALSE_BRANCH'"},
            },
            {"id": "e1", "type": "end", "config": {}},
        ]
        edges = [
            {"id": "e1-edge", "source": "s1", "target": "c1"},
            {"id": "e2-edge", "source": "c1", "target": "code_t", "sourceHandle": "true"},
            {"id": "e3-edge", "source": "c1", "target": "code_f", "sourceHandle": "false"},
            {"id": "e4-edge", "source": "code_t", "target": "e1"},
            {"id": "e5-edge", "source": "code_f", "target": "e1"},
        ]
        wf = _make_workflow(nodes, edges)

        with patch(
            "be.app.workflow.engine.WorkflowService", return_value=_mock_workflow_service()
        ):
            engine = WorkflowEngine(wf)
            events = []
            async for sse in engine.execute({}):
                data = json.loads(sse.replace("data: ", "").strip())
                events.append(data)

        node_completes = [e for e in events if e["event"] == "node_complete"]
        executed_ids = [e["node_id"] for e in node_completes]

        # expression = True → true branch
        assert "code_t" in executed_ids
        assert "code_f" not in executed_ids
