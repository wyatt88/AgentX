"""
Integration tests: Provider → Agent → Workflow → Execute.

Uses moto to mock DynamoDB, so no real AWS calls are made.
Verifies the full pipeline:
  1. Create ModelProvider in ModelProviderTable
  2. Create Agent using that provider
  3. Create Workflow with an Agent node
  4. Execute the workflow (mocking the actual LLM call)

Run with:
    pytest be/tests/test_integration.py -v
"""

import json
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import boto3
import pytest
from moto import mock_aws as mock_dynamodb

from be.app.agent.agent import (
    AgentPO,
    AgentPOService,
    AgentTool,
    AgentToolType,
    AgentType,
    ModelProvider,
)
from be.app.model.models import ModelProviderPO
from be.app.model.service import ModelProviderService
from be.app.workflow.engine import WorkflowEngine
from be.app.workflow.models import WorkflowPO, WorkflowService, WorkflowStatus


# ── DynamoDB table creation helpers ───────────────────────────────────────────


def _create_agent_table(dynamodb):
    dynamodb.create_table(
        TableName="AgentTable",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _create_model_provider_table(dynamodb):
    dynamodb.create_table(
        TableName="ModelProviderTable",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _create_workflow_table(dynamodb):
    dynamodb.create_table(
        TableName="WorkflowTable",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _create_execution_table(dynamodb):
    dynamodb.create_table(
        TableName="WorkflowExecutionTable",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "workflow_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "workflow_id-index",
                "KeySchema": [
                    {"AttributeName": "workflow_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )


def _create_all_tables(dynamodb):
    _create_agent_table(dynamodb)
    _create_model_provider_table(dynamodb)
    _create_workflow_table(dynamodb)
    _create_execution_table(dynamodb)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def aws_env(monkeypatch):
    """Set dummy AWS credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_REGION", "us-west-2")


@pytest.fixture
def dynamodb_mock(aws_env):
    """Provide a moto DynamoDB mock with all required tables."""
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
        _create_all_tables(dynamodb)
        yield dynamodb


# ── Step 1: Create ModelProvider ──────────────────────────────────────────────


class TestStep1CreateProvider:
    """创建 ModelProvider 到 ModelProviderTable"""

    def test_create_openai_provider(self, dynamodb_mock):
        svc = ModelProviderService()
        provider = ModelProviderPO(
            name="Test OpenAI",
            type="openai",
            config={"base_url": "https://api.openai.com/v1", "api_key": "sk-test"},
            models=["gpt-4o"],
            is_default=False,
        )
        result = svc.create_provider(provider)

        assert result.id != ""
        assert result.name == "Test OpenAI"

        # Verify retrievable
        fetched = svc.get_provider(result.id)
        assert fetched is not None
        assert fetched.type == "openai"
        assert fetched.config["api_key"] == "sk-test"

    def test_create_bedrock_default_provider(self, dynamodb_mock):
        svc = ModelProviderService()
        provider = ModelProviderPO(
            name="AWS Bedrock",
            type="bedrock",
            config={"region": "us-west-2"},
            models=["us.anthropic.claude-3-7-sonnet-20250219-v1:0"],
            is_default=True,
        )
        result = svc.create_provider(provider)

        assert result.is_default is True

        providers = svc.list_providers()
        assert len(providers) == 1


# ── Step 2: Create Agent using Provider ───────────────────────────────────────


class TestStep2CreateAgent:
    """创建 Agent 并关联 ModelProvider"""

    def test_create_agent_with_openai_provider(self, dynamodb_mock):
        # First create provider
        provider_svc = ModelProviderService()
        provider = provider_svc.create_provider(
            ModelProviderPO(
                name="OpenAI",
                type="openai",
                config={
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "sk-test",
                },
                models=["gpt-4o"],
                is_default=True,
            )
        )

        # Then create agent
        agent_svc = AgentPOService()
        agent = AgentPO(
            id=uuid.uuid4().hex,
            name="test-agent",
            display_name="Test Agent",
            description="Agent for integration test",
            agent_type=AgentType.plain,
            model_provider=ModelProvider.openai,
            model_id="gpt-4o",
            sys_prompt="You are a test assistant.",
            tools=[],
        )
        agent_svc.add_agent(agent)

        # Verify
        fetched = agent_svc.get_agent(agent.id)
        assert fetched is not None
        assert fetched.model_provider == ModelProvider.openai
        assert fetched.model_id == "gpt-4o"


# ── Step 3: _build_model integration with ModelProviderTable ──────────────────


class TestStep3BuildModelIntegration:
    """验证 _build_model 正确查询 ModelProviderTable"""

    def test_build_model_enriches_from_provider_table(self, dynamodb_mock):
        """_build_model 应从 ModelProviderTable 获取 config 并合并"""
        # Insert an openai provider
        provider_svc = ModelProviderService()
        provider_svc.create_provider(
            ModelProviderPO(
                name="OpenAI Default",
                type="openai",
                config={
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "sk-from-provider-table",
                },
                is_default=True,
            )
        )

        agent_svc = AgentPOService()

        # Patch OpenAIModel at the module that _build_model imports from
        import sys
        mock_openai_model = MagicMock()
        original_module = sys.modules.get("strands.models.openai")
        mock_module = MagicMock()
        mock_module.OpenAIModel = mock_openai_model
        sys.modules["strands.models.openai"] = mock_module

        try:
            model = agent_svc._build_model(
                provider=ModelProvider.openai,
                model_id="gpt-4o",
                extras=None,
            )

            # OpenAIModel should have been called with provider-table config
            mock_openai_model.assert_called_once()
            call_kwargs = mock_openai_model.call_args
            client_args = call_kwargs[1]["client_args"]
            assert client_args["api_key"] == "sk-from-provider-table"
            assert client_args["base_url"] == "https://api.openai.com/v1"
        finally:
            if original_module:
                sys.modules["strands.models.openai"] = original_module

    def test_build_model_agent_extras_override_provider(self, dynamodb_mock):
        """Agent 级别 extras 应覆盖 ProviderTable 配置"""
        provider_svc = ModelProviderService()
        provider_svc.create_provider(
            ModelProviderPO(
                name="OpenAI",
                type="openai",
                config={
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "sk-provider-level",
                },
                is_default=True,
            )
        )

        agent_svc = AgentPOService()

        import sys
        mock_openai_model = MagicMock()
        original_module = sys.modules.get("strands.models.openai")
        mock_module = MagicMock()
        mock_module.OpenAIModel = mock_openai_model
        sys.modules["strands.models.openai"] = mock_module

        try:
            model = agent_svc._build_model(
                provider=ModelProvider.openai,
                model_id="gpt-4o",
                extras={"api_key": "sk-agent-override"},
            )

            call_kwargs = mock_openai_model.call_args
            client_args = call_kwargs[1]["client_args"]
            # Agent-level key should win
            assert client_args["api_key"] == "sk-agent-override"
        finally:
            if original_module:
                sys.modules["strands.models.openai"] = original_module

    def test_build_model_fallback_when_no_table(self, dynamodb_mock):
        """ModelProviderTable 无匹配记录时应 fallback 到默认 Bedrock"""
        agent_svc = AgentPOService()

        # No provider records in table → bedrock fallback
        model = agent_svc._build_model(
            provider=ModelProvider.bedrock,
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        )

        # Should return a BedrockModel (or at least not crash)
        assert model is not None


# ── Step 4: Create + Execute Workflow ─────────────────────────────────────────


class TestStep4WorkflowExecution:
    """创建工作流 → 执行 → 验证"""

    def test_create_workflow(self, dynamodb_mock):
        """WorkflowService CRUD"""
        svc = WorkflowService()
        definition = json.dumps({
            "nodes": [
                {"id": "s1", "type": "start", "config": {}},
                {"id": "e1", "type": "end", "config": {}},
            ],
            "edges": [{"id": "edge1", "source": "s1", "target": "e1"}],
        })
        wf = WorkflowPO(name="int-test-wf", definition=definition)
        created = svc.add_workflow(wf)

        assert created.id != ""

        fetched = svc.get_workflow(created.id)
        assert fetched is not None
        assert fetched.name == "int-test-wf"

    @pytest.mark.asyncio
    async def test_full_pipeline_provider_agent_workflow(self, dynamodb_mock):
        """
        完整集成: 创建 Provider → 创建 Agent → 创建 Workflow → 执行
        """
        # 1. Create provider
        provider_svc = ModelProviderService()
        provider = provider_svc.create_provider(
            ModelProviderPO(
                name="Bedrock Default",
                type="bedrock",
                config={"region": "us-west-2"},
                models=["us.anthropic.claude-3-7-sonnet-20250219-v1:0"],
                is_default=True,
            )
        )

        # 2. Create agent
        agent_svc = AgentPOService()
        agent_id = uuid.uuid4().hex
        agent = AgentPO(
            id=agent_id,
            name="pipeline-agent",
            display_name="Pipeline Agent",
            description="Integration pipeline agent",
            agent_type=AgentType.plain,
            model_provider=ModelProvider.bedrock,
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            sys_prompt="You are a helpful assistant.",
            tools=[],
        )
        agent_svc.add_agent(agent)

        # 3. Create workflow with agent node
        wf_svc = WorkflowService()
        definition = json.dumps({
            "nodes": [
                {"id": "s1", "type": "start", "config": {}},
                {
                    "id": "a1",
                    "type": "agent",
                    "config": {"agent_id": agent_id},
                },
                {"id": "e1", "type": "end", "config": {}},
            ],
            "edges": [
                {"id": "edge1", "source": "s1", "target": "a1"},
                {"id": "edge2", "source": "a1", "target": "e1"},
            ],
        })
        wf = WorkflowPO(
            name="pipeline-workflow",
            definition=definition,
            status=WorkflowStatus.published,
        )
        wf_svc.add_workflow(wf)

        # 4. Execute workflow (mock stream_chat)
        async def mock_stream_chat(aid, msg):
            yield {"data": "Integration test response"}
            yield {"usage": {"totalTokens": 200}}

        with patch.object(
            AgentPOService, "stream_chat", side_effect=mock_stream_chat
        ):
            engine = WorkflowEngine(wf)
            events = []
            async for sse in engine.execute({"query": "hello pipeline"}):
                data = json.loads(sse.replace("data: ", "").strip())
                events.append(data)

        # Verify
        event_types = [e["event"] for e in events]
        assert event_types[0] == "workflow_start"
        assert event_types[-1] == "workflow_complete"

        # Agent node should have produced output
        agent_complete = next(
            (e for e in events if e["event"] == "node_complete" and e["node_id"] == "a1"),
            None,
        )
        assert agent_complete is not None
        assert "Integration test response" in str(agent_complete["output"])


# ── Step 5: get_all_available_tools() 增强验证 ───────────────────────────────


class TestStep5ToolListEnhancement:
    """验证 get_all_available_tools() 包含 group/status 信息"""

    def test_tools_include_builtin_strands_tools(self, dynamodb_mock):
        """工具列表应包含内置 Strands 工具"""
        # Mock MCPService to avoid DynamoDB calls for HttpMCPTable
        with patch("be.app.agent.agent.MCPService") as MockMCPSvc:
            MockMCPSvc.return_value.list_mcp_servers.return_value = []
            agent_svc = AgentPOService()
            tools = agent_svc.get_all_available_tools()

        # Should have at least the built-in tools
        tool_names = [t.name for t in tools]
        assert "calculator" in tool_names
        assert "current_time" in tool_names
        assert "http_request" in tool_names

    def test_tools_include_agent_as_tool(self, dynamodb_mock):
        """plain Agent 应作为 Agent 类型工具出现"""
        agent_svc = AgentPOService()

        # Create a plain agent
        agent = AgentPO(
            id=uuid.uuid4().hex,
            name="helper-agent",
            display_name="Helper",
            description="A helper agent",
            agent_type=AgentType.plain,
            model_provider=ModelProvider.bedrock,
            model_id="test-model",
            tools=[],
        )
        agent_svc.add_agent(agent)

        with patch("be.app.agent.agent.MCPService") as MockMCPSvc:
            MockMCPSvc.return_value.list_mcp_servers.return_value = []
            tools = agent_svc.get_all_available_tools()

        agent_tools = [t for t in tools if t.type == AgentToolType.agent]
        assert len(agent_tools) >= 1
        assert any(t.name == "helper-agent" for t in agent_tools)

    def test_tools_mcp_with_group_and_status(self, dynamodb_mock):
        """MCP 工具应包含 group 和 status 信息，且只返回 running 状态"""
        agent_svc = AgentPOService()

        # Mock MCP servers — one running, one error
        mock_running_server = MagicMock()
        mock_running_server.name = "db-mcp"
        mock_running_server.desc = "Database MCP"
        mock_running_server.host = "http://localhost:3000/mcp"
        mock_running_server.group = "database"
        mock_running_server.status = "running"

        mock_error_server = MagicMock()
        mock_error_server.name = "broken-mcp"
        mock_error_server.desc = "Broken MCP"
        mock_error_server.host = "http://localhost:4000/mcp"
        mock_error_server.group = "analytics"
        mock_error_server.status = "error"

        with patch("be.app.agent.agent.MCPService") as MockMCPSvc:
            MockMCPSvc.return_value.list_mcp_servers.return_value = [
                mock_running_server,
                mock_error_server,
            ]
            tools = agent_svc.get_all_available_tools()

        # Filter MCP tools
        mcp_tools = [t for t in tools if t.type == AgentToolType.mcp]

        # Should only include the running server
        assert len(mcp_tools) == 1
        assert mcp_tools[0].name == "db-mcp"

        # Should have group and status in extra
        assert mcp_tools[0].extra is not None
        assert mcp_tools[0].extra["group"] == "database"
        assert mcp_tools[0].extra["status"] == "running"

    def test_tools_mcp_excludes_non_running(self, dynamodb_mock):
        """非 running 状态的 MCP server 不应返回"""
        agent_svc = AgentPOService()

        mock_unknown = MagicMock()
        mock_unknown.name = "unknown-mcp"
        mock_unknown.desc = "Unknown status"
        mock_unknown.host = "http://localhost:5000/mcp"
        mock_unknown.group = "default"
        mock_unknown.status = "unknown"

        with patch("be.app.agent.agent.MCPService") as MockMCPSvc:
            MockMCPSvc.return_value.list_mcp_servers.return_value = [mock_unknown]
            tools = agent_svc.get_all_available_tools()

        mcp_tools = [t for t in tools if t.type == AgentToolType.mcp]
        assert len(mcp_tools) == 0
