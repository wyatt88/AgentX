"""
Unit tests for workflow node executors (5 types).

Tests:
  - StartNodeExecutor  — 透传 input_data
  - AgentNodeExecutor  — mock stream_chat, 验证响应收集
  - ConditionNodeExecutor — true/false 分支 + 异常表达式
  - CodeNodeExecutor  — 自定义代码执行 + result 返回
  - EndNodeExecutor   — 输出收集 + output_keys 过滤

Run with:
    pytest be/tests/test_nodes.py -v
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from be.app.workflow.nodes import (
    AgentNodeExecutor,
    CodeNodeExecutor,
    ConditionNodeExecutor,
    EndNodeExecutor,
    NodeType,
    StartNodeExecutor,
    get_executor,
)


# ── StartNodeExecutor ─────────────────────────────────────────────────────────


class TestStartNodeExecutor:
    """StartNodeExecutor: 透传 input_data"""

    @pytest.mark.asyncio
    async def test_passthrough_input(self):
        executor = StartNodeExecutor()
        context = {"input": {"query": "hello", "user_id": 42}}
        node = {"id": "start_1", "type": "start", "config": {}}

        result = await executor.execute(node, context)

        assert result == {"query": "hello", "user_id": 42}

    @pytest.mark.asyncio
    async def test_empty_input(self):
        executor = StartNodeExecutor()
        context = {"input": {}}
        node = {"id": "start_1", "type": "start", "config": {}}

        result = await executor.execute(node, context)

        assert result == {}

    @pytest.mark.asyncio
    async def test_missing_input_key(self):
        executor = StartNodeExecutor()
        context = {}
        node = {"id": "start_1", "type": "start", "config": {}}

        result = await executor.execute(node, context)

        assert result == {}


# ── AgentNodeExecutor ─────────────────────────────────────────────────────────


class TestAgentNodeExecutor:
    """AgentNodeExecutor: mock AgentPOService.stream_chat 验证响应收集"""

    @pytest.mark.asyncio
    async def test_agent_node_collects_response(self):
        """Agent 节点应收集 stream_chat 的完整文本响应"""

        # Mock stream_chat 返回异步生成器
        async def mock_stream_chat(agent_id, user_message):
            yield {"data": "Hello "}
            yield {"data": "World!"}
            yield {"usage": {"totalTokens": 150}}

        with patch.object(
            AgentNodeExecutor, "__init__", lambda self: None
        ):
            executor = AgentNodeExecutor()
            executor._agent_service = MagicMock()
            executor._agent_service.stream_chat = mock_stream_chat

        node = {
            "id": "agent_1",
            "type": "agent",
            "config": {"agent_id": "test-agent-id"},
        }
        context = {"input": {"query": "test"}}

        result = await executor.execute(node, context)

        assert result["response"] == "Hello World!"
        assert result["agent_id"] == "test-agent-id"
        assert result["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_agent_node_with_template(self):
        """Agent 节点应支持 user_message_template 模板渲染"""

        async def mock_stream_chat(agent_id, user_message):
            yield {"data": f"Echo: {user_message}"}

        with patch.object(
            AgentNodeExecutor, "__init__", lambda self: None
        ):
            executor = AgentNodeExecutor()
            executor._agent_service = MagicMock()
            executor._agent_service.stream_chat = mock_stream_chat

        node = {
            "id": "agent_1",
            "type": "agent",
            "config": {
                "agent_id": "agent-tmpl",
                "user_message_template": "Please answer: {{input.query}}",
            },
        }
        context = {"input": {"query": "What is 1+1?"}}

        result = await executor.execute(node, context)

        assert "What is 1+1?" in result["response"]

    @pytest.mark.asyncio
    async def test_agent_node_missing_agent_id(self):
        """缺少 agent_id 应抛出 ValueError"""
        with patch.object(
            AgentNodeExecutor, "__init__", lambda self: None
        ):
            executor = AgentNodeExecutor()
            executor._agent_service = MagicMock()

        node = {"id": "agent_1", "type": "agent", "config": {}}
        context = {"input": {}}

        with pytest.raises(ValueError, match="缺少 agent_id"):
            await executor.execute(node, context)

    @pytest.mark.asyncio
    async def test_agent_node_dict_data(self):
        """stream_chat 返回 dict data 时也能正确收集文本"""

        async def mock_stream_chat(agent_id, user_message):
            yield {"data": {"text": "Part1"}}
            yield {"data": {"text": "Part2"}}

        with patch.object(
            AgentNodeExecutor, "__init__", lambda self: None
        ):
            executor = AgentNodeExecutor()
            executor._agent_service = MagicMock()
            executor._agent_service.stream_chat = mock_stream_chat

        node = {
            "id": "agent_1",
            "type": "agent",
            "config": {"agent_id": "agent-dict"},
        }
        context = {"input": {}}

        result = await executor.execute(node, context)
        assert result["response"] == "Part1Part2"


# ── ConditionNodeExecutor ─────────────────────────────────────────────────────


class TestConditionNodeExecutor:
    """ConditionNodeExecutor: 表达式 eval + true/false 分支"""

    @pytest.mark.asyncio
    async def test_condition_true(self):
        executor = ConditionNodeExecutor()
        node = {
            "id": "cond_1",
            "type": "condition",
            "config": {"expression": "context.get('input', {}).get('score', 0) > 60"},
        }
        context = {"input": {"score": 80}}

        result = await executor.execute(node, context)

        assert result == "true"

    @pytest.mark.asyncio
    async def test_condition_false(self):
        executor = ConditionNodeExecutor()
        node = {
            "id": "cond_1",
            "type": "condition",
            "config": {"expression": "context.get('input', {}).get('score', 0) > 60"},
        }
        context = {"input": {"score": 30}}

        result = await executor.execute(node, context)

        assert result == "false"

    @pytest.mark.asyncio
    async def test_condition_default_true(self):
        """无表达式时默认返回 true"""
        executor = ConditionNodeExecutor()
        node = {"id": "cond_1", "type": "condition", "config": {}}
        context = {}

        result = await executor.execute(node, context)

        assert result == "true"

    @pytest.mark.asyncio
    async def test_condition_uses_flat_context(self):
        """表达式可直接引用 context 中扁平注入的节点输出"""
        executor = ConditionNodeExecutor()
        node = {
            "id": "cond_1",
            "type": "condition",
            "config": {"expression": "start_1 is not None"},
        }
        context = {"input": {}, "start_1": {"msg": "hello"}}

        result = await executor.execute(node, context)

        assert result == "true"

    @pytest.mark.asyncio
    async def test_condition_invalid_expression(self):
        """无效表达式应抛出 ValueError"""
        executor = ConditionNodeExecutor()
        node = {
            "id": "cond_1",
            "type": "condition",
            "config": {"expression": "undefined_var + 1"},
        }
        context = {}

        with pytest.raises(ValueError, match="表达式执行失败"):
            await executor.execute(node, context)


# ── CodeNodeExecutor ──────────────────────────────────────────────────────────


class TestCodeNodeExecutor:
    """CodeNodeExecutor: 执行自定义 Python 代码片段"""

    @pytest.mark.asyncio
    async def test_code_simple_result(self):
        executor = CodeNodeExecutor()
        node = {
            "id": "code_1",
            "type": "code",
            "config": {"code": "result = 42"},
        }
        context = {"input": {}}

        result = await executor.execute(node, context)

        assert result == 42

    @pytest.mark.asyncio
    async def test_code_uses_inputs(self):
        """代码可访问 inputs (即 context)"""
        executor = CodeNodeExecutor()
        node = {
            "id": "code_1",
            "type": "code",
            "config": {"code": "result = inputs.get('input', {}).get('x', 0) * 2"},
        }
        context = {"input": {"x": 21}}

        result = await executor.execute(node, context)

        assert result == 42

    @pytest.mark.asyncio
    async def test_code_uses_upstream_output(self):
        """代码可直接引用上游节点输出"""
        executor = CodeNodeExecutor()
        node = {
            "id": "code_1",
            "type": "code",
            "config": {
                "code": "result = agent_1.get('response', '') + ' processed'"
            },
        }
        context = {
            "input": {},
            "agent_1": {"response": "Hello"},
        }

        result = await executor.execute(node, context)

        assert result == "Hello processed"

    @pytest.mark.asyncio
    async def test_code_json_parsing(self):
        """代码节点中可使用 json 模块"""
        executor = CodeNodeExecutor()
        node = {
            "id": "code_1",
            "type": "code",
            "config": {
                "code": 'result = json.loads(\'{"a": 1}\')'
            },
        }
        context = {"input": {}}

        result = await executor.execute(node, context)

        assert result == {"a": 1}

    @pytest.mark.asyncio
    async def test_code_empty_returns_none(self):
        executor = CodeNodeExecutor()
        node = {"id": "code_1", "type": "code", "config": {"code": ""}}
        context = {"input": {}}

        result = await executor.execute(node, context)

        assert result is None

    @pytest.mark.asyncio
    async def test_code_execution_error(self):
        """代码执行错误应抛出 ValueError"""
        executor = CodeNodeExecutor()
        node = {
            "id": "code_1",
            "type": "code",
            "config": {"code": "result = 1 / 0"},
        }
        context = {"input": {}}

        with pytest.raises(ValueError, match="执行失败"):
            await executor.execute(node, context)


# ── EndNodeExecutor ───────────────────────────────────────────────────────────


class TestEndNodeExecutor:
    """EndNodeExecutor: 收集最终输出"""

    @pytest.mark.asyncio
    async def test_collects_all_outputs(self):
        executor = EndNodeExecutor()
        node = {"id": "end_1", "type": "end", "config": {}}
        context = {
            "input": {"query": "test"},
            "start_1": {"query": "test"},
            "agent_1": {"response": "Hello!"},
        }

        result = await executor.execute(node, context)

        # 应排除 'input'，包含其他所有节点输出
        assert "input" not in result
        assert "start_1" in result
        assert "agent_1" in result
        assert result["agent_1"] == {"response": "Hello!"}

    @pytest.mark.asyncio
    async def test_output_keys_filter(self):
        """指定 output_keys 时只收集指定节点输出"""
        executor = EndNodeExecutor()
        node = {
            "id": "end_1",
            "type": "end",
            "config": {"output_keys": ["agent_1"]},
        }
        context = {
            "input": {"query": "test"},
            "start_1": {"query": "test"},
            "agent_1": {"response": "Important"},
            "code_1": {"result": 42},
        }

        result = await executor.execute(node, context)

        assert list(result.keys()) == ["agent_1"]
        assert result["agent_1"] == {"response": "Important"}

    @pytest.mark.asyncio
    async def test_empty_context(self):
        executor = EndNodeExecutor()
        node = {"id": "end_1", "type": "end", "config": {}}
        context = {"input": {}}

        result = await executor.execute(node, context)

        assert result == {}


# ── get_executor registry ─────────────────────────────────────────────────────


class TestGetExecutor:
    """get_executor() 注册表测试"""

    def test_all_types_registered(self):
        for nt in NodeType:
            executor = get_executor(nt.value)
            assert executor is not None

    def test_unknown_type_raises(self):
        with pytest.raises(KeyError, match="不支持的节点类型"):
            get_executor("unknown_type")

    def test_returns_correct_types(self):
        assert isinstance(get_executor("start"), StartNodeExecutor)
        assert isinstance(get_executor("agent"), AgentNodeExecutor)
        assert isinstance(get_executor("condition"), ConditionNodeExecutor)
        assert isinstance(get_executor("code"), CodeNodeExecutor)
        assert isinstance(get_executor("end"), EndNodeExecutor)
