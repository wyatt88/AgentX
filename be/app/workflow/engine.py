# workflow/engine.py — DAG 工作流执行引擎
"""
WorkflowEngine: 解析工作流 definition JSON，以 BFS 方式遍历 DAG 图，
逐节点执行并 yield SSE 事件，支持条件分支路由。
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from .models import (
    ExecutionStatus,
    WorkflowExecution,
    WorkflowPO,
    WorkflowService,
)
from .nodes import get_executor


class WorkflowEngine:
    """
    DAG 工作流执行引擎。

    使用 BFS 遍历工作流 DAG 图，逐节点调用对应 NodeExecutor，
    并通过 AsyncGenerator yield SSE 事件供 StreamingResponse 消费。
    """

    def __init__(self, workflow: WorkflowPO) -> None:
        self.workflow = workflow
        self.definition: dict = json.loads(workflow.definition)
        self.nodes: Dict[str, dict] = {n["id"]: n for n in self.definition.get("nodes", [])}
        self.edges: List[dict] = self.definition.get("edges", [])
        self.context: Dict[str, Any] = {}  # node_id → output

    # ── 公开接口 ───────────────────────────────────────────────────────────

    async def execute(self, input_data: dict) -> AsyncGenerator[str, None]:
        """
        执行工作流，yield SSE 格式事件字符串。

        事件类型:
          - workflow_start   — 执行开始
          - node_start       — 节点开始执行
          - node_complete    — 节点执行完成
          - node_error       — 节点执行异常
          - workflow_complete — 工作流执行完成
          - workflow_error   — 工作流执行异常

        :param input_data: 工作流输入数据
        :yield: SSE 格式字符串 "data: {...}\\n\\n"
        """
        execution_id = uuid.uuid4().hex
        wf_service = WorkflowService()
        start_ts = time.time()

        # 创建执行记录
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=self.workflow.id,
            status=ExecutionStatus.running,
            input_data=json.dumps(input_data, ensure_ascii=False),
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        wf_service.add_execution(execution)

        self.context["input"] = input_data
        node_states: Dict[str, dict] = {}

        # yield workflow_start
        yield self._sse({
            "event": "workflow_start",
            "execution_id": execution_id,
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name,
        })

        try:
            # 查找起始节点
            start_node = self._find_start_node()
            queue: List[str] = [start_node["id"]]
            visited: Set[str] = set()

            while queue:
                node_id = queue.pop(0)
                if node_id in visited:
                    continue
                visited.add(node_id)

                node = self.nodes.get(node_id)
                if node is None:
                    continue

                node_type = node.get("type", "unknown")

                # yield node_start
                yield self._sse({
                    "event": "node_start",
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "node_type": node_type,
                    "node_name": node.get("name", node_id),
                })

                node_start_ts = time.time()
                try:
                    # 执行节点
                    executor = get_executor(node_type)
                    result = await executor.execute(node, self.context)
                    self.context[node_id] = result

                    node_duration_ms = int((time.time() - node_start_ts) * 1000)
                    node_states[node_id] = {
                        "status": "completed",
                        "duration_ms": node_duration_ms,
                        "output_summary": self._summarize(result),
                    }

                    # yield node_complete
                    yield self._sse({
                        "event": "node_complete",
                        "execution_id": execution_id,
                        "node_id": node_id,
                        "node_type": node_type,
                        "output": self._safe_serialize(result),
                        "duration_ms": node_duration_ms,
                    })

                    # 查找后继节点
                    next_nodes = self._get_next_nodes(node_id, result)
                    queue.extend(next_nodes)

                except Exception as exc:
                    node_duration_ms = int((time.time() - node_start_ts) * 1000)
                    node_states[node_id] = {
                        "status": "failed",
                        "duration_ms": node_duration_ms,
                        "error": str(exc),
                    }

                    yield self._sse({
                        "event": "node_error",
                        "execution_id": execution_id,
                        "node_id": node_id,
                        "node_type": node_type,
                        "error": str(exc),
                        "duration_ms": node_duration_ms,
                    })

                    # 节点失败 → 工作流失败
                    raise

            # 工作流执行完成
            total_duration_ms = int((time.time() - start_ts) * 1000)
            total_tokens = self._collect_total_tokens()

            execution.status = ExecutionStatus.completed
            execution.completed_at = datetime.now(timezone.utc).isoformat()
            execution.output_data = json.dumps(
                self._safe_serialize(self._collect_output()), ensure_ascii=False
            )
            execution.node_states = json.dumps(node_states, ensure_ascii=False)
            execution.total_tokens = total_tokens
            execution.total_duration_ms = total_duration_ms
            wf_service.update_execution(execution)

            yield self._sse({
                "event": "workflow_complete",
                "execution_id": execution_id,
                "total_duration_ms": total_duration_ms,
                "total_tokens": total_tokens,
                "output": self._safe_serialize(self._collect_output()),
            })

        except Exception as exc:
            total_duration_ms = int((time.time() - start_ts) * 1000)

            execution.status = ExecutionStatus.failed
            execution.completed_at = datetime.now(timezone.utc).isoformat()
            execution.error_message = str(exc)
            execution.node_states = json.dumps(node_states, ensure_ascii=False)
            execution.total_duration_ms = total_duration_ms
            wf_service.update_execution(execution)

            yield self._sse({
                "event": "workflow_error",
                "execution_id": execution_id,
                "error": str(exc),
                "total_duration_ms": total_duration_ms,
            })

    # ── 内部方法 ───────────────────────────────────────────────────────────

    def _find_start_node(self) -> dict:
        """查找 start 类型节点，若不存在则取无入边的第一个节点"""
        for node in self.nodes.values():
            if node.get("type") == "start":
                return node

        # 找无入边节点
        target_ids = {edge.get("target") for edge in self.edges}
        for node in self.nodes.values():
            if node["id"] not in target_ids:
                return node

        raise ValueError("工作流中找不到起始节点")

    def _get_next_nodes(self, node_id: str, result: Any) -> List[str]:
        """
        根据当前节点 ID 和执行结果，查找后继节点列表。
        对于条件节点，根据 result ('true' / 'false') 筛选对应分支的边。
        """
        next_ids: List[str] = []
        node = self.nodes.get(node_id, {})
        is_condition = node.get("type") == "condition"

        for edge in self.edges:
            if edge.get("source") != node_id:
                continue

            if is_condition:
                # 条件节点：edge 需要有 condition / label 字段标识分支
                edge_condition = (
                    edge.get("condition")
                    or edge.get("label")
                    or edge.get("sourceHandle")
                    or ""
                ).lower()
                result_str = str(result).lower()

                if edge_condition == result_str:
                    next_ids.append(edge["target"])
                elif not edge_condition:
                    # 无条件边作为 fallback
                    next_ids.append(edge["target"])
            else:
                next_ids.append(edge["target"])

        return next_ids

    def _collect_output(self) -> dict:
        """收集工作流最终输出（排除 'input' key）"""
        return {
            node_id: output
            for node_id, output in self.context.items()
            if node_id != "input"
        }

    def _collect_total_tokens(self) -> int:
        """从 context 中的 Agent 节点输出汇总 token 用量"""
        total = 0
        for value in self.context.values():
            if isinstance(value, dict) and "total_tokens" in value:
                total += int(value["total_tokens"])
        return total

    @staticmethod
    def _summarize(result: Any, max_len: int = 200) -> str:
        """将节点输出摘要为简短字符串"""
        s = str(result)
        return s[:max_len] + "..." if len(s) > max_len else s

    @staticmethod
    def _safe_serialize(obj: Any) -> Any:
        """确保对象可被 JSON 序列化"""
        try:
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)

    @staticmethod
    def _sse(data: dict) -> str:
        """将 dict 格式化为 SSE 数据行"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
