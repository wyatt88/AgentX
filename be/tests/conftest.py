"""
Shared pytest fixtures for AgentX backend tests.

Mocks the strands SDK and MCP client imports so tests can run
without the actual strands-agents package installed.
"""

import sys
import types
from unittest.mock import MagicMock

import pytest


# ── Mock strands SDK and dependencies before any app code is imported ────────

def _install_mock_modules():
    """Install mock modules for strands SDK and MCP client into sys.modules."""

    # strands top-level
    strands_mock = types.ModuleType("strands")
    strands_mock.Agent = MagicMock()
    strands_mock.tool = MagicMock(side_effect=lambda **kwargs: lambda fn: fn)

    strands_models_mock = types.ModuleType("strands.models")
    strands_models_bedrock_mock = types.ModuleType("strands.models.bedrock")
    strands_models_openai_mock = types.ModuleType("strands.models.openai")

    # BedrockModel mock
    class FakeBedrockModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    # BotocoreConfig mock
    class FakeBotocoreConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    # OpenAIModel mock
    class FakeOpenAIModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    strands_models_mock.BedrockModel = FakeBedrockModel
    strands_models_bedrock_mock.BedrockModel = FakeBedrockModel
    strands_models_bedrock_mock.BotocoreConfig = FakeBotocoreConfig
    strands_models_openai_mock.OpenAIModel = FakeOpenAIModel

    # MCP client mocks
    strands_tools_mcp_mock = types.ModuleType("strands.tools.mcp")
    strands_tools_mcp_client_mock = types.ModuleType("strands.tools.mcp.mcp_client")
    strands_tools_mcp_client_mock.MCPClient = MagicMock()
    strands_tools_mock = types.ModuleType("strands.tools")

    mcp_mock = types.ModuleType("mcp")
    mcp_client_mock = types.ModuleType("mcp.client")
    mcp_streamable_mock = types.ModuleType("mcp.client.streamable_http")
    mcp_streamable_mock.streamablehttp_client = MagicMock()

    # strands_tools mock
    strands_tools_pkg = types.ModuleType("strands_tools")

    # Install into sys.modules (order matters — parent before child)
    mocks = {
        "strands": strands_mock,
        "strands.models": strands_models_mock,
        "strands.models.bedrock": strands_models_bedrock_mock,
        "strands.models.openai": strands_models_openai_mock,
        "strands.tools": strands_tools_mock,
        "strands.tools.mcp": strands_tools_mcp_mock,
        "strands.tools.mcp.mcp_client": strands_tools_mcp_client_mock,
        "mcp": mcp_mock,
        "mcp.client": mcp_client_mock,
        "mcp.client.streamable_http": mcp_streamable_mock,
        "strands_tools": strands_tools_pkg,
    }

    for name, mod in mocks.items():
        sys.modules[name] = mod


# Install mocks at import time (before pytest collects test modules)
_install_mock_modules()


@pytest.fixture(scope="session", autouse=True)
def _set_env():
    """Ensure APP_ENV is unset so url_prefix is empty during tests.

    Also guarantee AWS_REGION is set (needed by DynamoDB service layers).
    """
    import os
    os.environ.pop("APP_ENV", None)
    os.environ.setdefault("AWS_REGION", "us-west-2")
