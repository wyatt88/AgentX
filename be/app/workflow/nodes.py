# workflow/nodes.py — 工作流节点类型定义与执行器
"""
定义 5 种节点类型（start / agent / condition / code / end）及对应的执行器。
每个执行器实现 execute(node, context) → result 语义。
"""
from __future__ import annotations

import json
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from ..agent.agent import AgentPOService


# ── 节点类型枚举 ──────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    """工作流支持的节点类型"""
    start = "start"
    agent = "agent"
    condition = "condition"
    code = "code"
    end = "end"


# ── 节点类型元信息（供前端 /node-types 接口使用）─────────────────────────────

NODE_TYPE_DEFINITIONS = [
    {
        "type": NodeType.start.value,
        "label": "开始节点",
        "description": "工作流入口，透传 input_data 到下游节点",
        "config_schema": {},
    },
    {
        "type": NodeType.agent.value,
        "label": "Agent 节点",
        "description": "调用已注册的 Agent（Strands SDK）处理消息并收集完整响应",
        "config_schema": {
            "agent_id": {"type": "string", "required": True, "description": "关联的 Agent ID"},
            "user_message_template": {
                "type": "string",
                "required": False,
                "description": "发送给 Agent 的消息模板，可使用 {{variable}} 引用上游输出",
            },
        },
    },
    {
        "type": NodeType.condition.value,
        "label": "条件节点",
        "description": "评估 Python 表达式，返回 true / false 分支标识",
        "config_schema": {
            "expression": {
                "type": "string",
                "required": True,
                "description": "Python 布尔表达式，可引用 context 变量",
            },
        },
    },
    {
        "type": NodeType.code.value,
        "label": "代码节点",
        "description": "执行自定义 Python 代码片段，传入 inputs dict，返回 result",
        "config_schema": {
            "code": {
                "type": "string",
                "required": True,
                "description": "要执行的 Python 代码，需将结果赋值给 result 变量",
            },
        },
    },
    {
        "type": NodeType.end.value,
        "label": "结束节点",
        "description": "工作流出口，收集并返回最终输出",
        "config_schema": {},
    },
]


# ── 执行器基类 ─────────────────────────────────────────────────────────────────

class NodeExecutor(ABC):
    """节点执行器抽象基类"""

    @abstractmethod
    async def execute(self, node: dict, context: Dict[str, Any]) -> Any:
        """
        执行节点逻辑。

        :param node: 节点定义 dict，包含 id / type / config 等字段
        :param context: 工作流执行上下文，key 为 'input' 或 node_id，value 为该节点输出
        :return: 节点执行结果
        """
        ...


# ── Start 节点 ─────────────────────────────────────────────────────────────────

class StartNodeExecutor(NodeExecutor):
    """开始节点：透传 input_data"""

    async def execute(self, node: dict, context: Dict[str, Any]) -> Any:
        return context.get("input", {})


# ── Agent 节点 ─────────────────────────────────────────────────────────────────

class AgentNodeExecutor(NodeExecutor):
    """
    Agent 节点：调用 AgentPOService.stream_chat() 收集完整响应。

    node.config 需要:
      - agent_id: str           — 目标 Agent ID
      - user_message_template: str (可选) — 消息模板，支持 {{key}} 占位符
    """

    def __init__(self) -> None:
        self._agent_service = AgentPOService()

    async def execute(self, node: dict, context: Dict[str, Any]) -> Any:
        config: dict = node.get("config", {}) or {}
        agent_id: str = config.get("agent_id", "")
        if not agent_id:
            raise ValueError(f"Agent 节点 [{node.get('id')}] 缺少 agent_id 配置")

        # 构建用户消息
        template: str = config.get("user_message_template", "")
        user_message = self._render_template(template, context) if template else json.dumps(
            context.get("input", {}), ensure_ascii=False
        )

        # 流式调用 Agent，收集完整文本响应
        collected_text_parts: list[str] = []
        total_tokens = 0

        async for event in self._agent_service.stream_chat(agent_id, user_message):
            # 提取文本内容
            if "data" in event:
                data = event["data"]
                if isinstance(data, str):
                    collected_text_parts.append(data)
                elif isinstance(data, dict) and "text" in data:
                    collected_text_parts.append(data["text"])
            # 尝试提取 token 用量
            if "usage" in event and isinstance(event["usage"], dict):
                total_tokens += event["usage"].get("totalTokens", 0)

        full_response = "".join(collected_text_parts)
        return {
            "response": full_response,
            "agent_id": agent_id,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _render_template(template: str, context: Dict[str, Any]) -> str:
        """简易模板渲染：将 {{key}} 替换为 context 中的值"""
        import re

        def _replacer(match: "re.Match[str]") -> str:
            key = match.group(1).strip()
            # 支持 input.xxx 或 node_id 直接引用
            parts = key.split(".", 1)
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, "")
                else:
                    return str(value)
            return str(value) if not isinstance(value, str) else value

        return re.sub(r"\{\{(.+?)\}\}", _replacer, template)


# ── Condition 节点 ─────────────────────────────────────────────────────────────

class ConditionNodeExecutor(NodeExecutor):
    """
    条件节点：评估 Python 表达式，返回 "true" 或 "false" 字符串标识。

    node.config 需要:
      - expression: str — Python 布尔表达式（可引用 context 变量）
    """

    async def execute(self, node: dict, context: Dict[str, Any]) -> Any:
        config: dict = node.get("config", {}) or {}
        expression: str = config.get("expression", "True")

        # 构建安全的 eval 命名空间
        safe_globals: dict = {"__builtins__": {}}
        safe_locals: dict = {
            "context": context,
            "inputs": context,
            "json": json,
        }
        # 扁平注入各节点输出，方便表达式直接引用
        for key, value in context.items():
            safe_locals[key] = value

        try:
            result = eval(expression, safe_globals, safe_locals)  # noqa: S307
            return "true" if bool(result) else "false"
        except Exception as exc:
            raise ValueError(
                f"条件节点 [{node.get('id')}] 表达式执行失败: {expression!r} — {exc}"
            ) from exc


# ── Code 节点 ──────────────────────────────────────────────────────────────────

class CodeNodeExecutor(NodeExecutor):
    """
    代码节点：exec() 执行 Python 代码片段，传入 inputs dict，返回 result 变量。

    node.config 需要:
      - code: str — Python 代码，需将结果赋值给 `result` 变量
    """

    async def execute(self, node: dict, context: Dict[str, Any]) -> Any:
        config: dict = node.get("config", {}) or {}
        code: str = config.get("code", "")
        if not code:
            return None

        # 构建执行命名空间
        exec_namespace: dict = {
            "inputs": context,
            "context": context,
            "json": json,
            "result": None,
        }
        # 扁平注入各节点输出
        for key, value in context.items():
            exec_namespace[key] = value

        try:
            exec(code, {"__builtins__": {}}, exec_namespace)  # noqa: S102
            return exec_namespace.get("result")
        except Exception as exc:
            raise ValueError(
                f"代码节点 [{node.get('id')}] 执行失败: {exc}\n{traceback.format_exc()}"
            ) from exc


# ── End 节点 ───────────────────────────────────────────────────────────────────

class EndNodeExecutor(NodeExecutor):
    """
    结束节点：收集最终输出。

    逻辑：从 context 中收集所有非 'input' 的节点输出，作为工作流最终结果返回。
    若 node.config 中指定了 output_keys，则只收集指定 key。
    """

    async def execute(self, node: dict, context: Dict[str, Any]) -> Any:
        config: dict = node.get("config", {}) or {}
        output_keys: Optional[list] = config.get("output_keys")

        if output_keys:
            return {k: context.get(k) for k in output_keys}

        # 默认：收集所有节点输出（排除 'input'）
        return {
            node_id: output
            for node_id, output in context.items()
            if node_id != "input"
        }


# ── 执行器注册表 ──────────────────────────────────────────────────────────────

_EXECUTOR_REGISTRY: Dict[str, NodeExecutor] = {
    NodeType.start.value: StartNodeExecutor(),
    NodeType.agent.value: AgentNodeExecutor(),
    NodeType.condition.value: ConditionNodeExecutor(),
    NodeType.code.value: CodeNodeExecutor(),
    NodeType.end.value: EndNodeExecutor(),
}


def get_executor(node_type: str) -> NodeExecutor:
    """
    根据节点类型获取对应的执行器实例。

    :param node_type: 节点类型字符串
    :return: NodeExecutor 实例
    :raises KeyError: 不支持的节点类型
    """
    executor = _EXECUTOR_REGISTRY.get(node_type)
    if executor is None:
        raise KeyError(f"不支持的节点类型: {node_type!r}，可用类型: {list(_EXECUTOR_REGISTRY.keys())}")
    return executor
