# routers/workflow.py — 工作流 API 路由
"""
提供 8 个 RESTful 接口:
  - GET  /workflow/list            — 列出所有工作流
  - GET  /workflow/get/{id}        — 获取工作流详情
  - POST /workflow/create          — 创建工作流
  - PUT  /workflow/update/{id}     — 更新工作流
  - DELETE /workflow/delete/{id}   — 删除工作流
  - POST /workflow/execute/{id}    — 执行工作流（SSE 流式返回）
  - GET  /workflow/node-types      — 获取可用节点类型定义
  - GET  /workflow/executions/{id} — 获取工作流执行历史
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ..workflow.models import (
    WorkflowExecution,
    WorkflowPO,
    WorkflowService,
    WorkflowStatus,
    TriggerType,
)
from ..workflow.engine import WorkflowEngine
from ..workflow.nodes import NODE_TYPE_DEFINITIONS

# ── 初始化 ─────────────────────────────────────────────────────────────────────

workflow_service = WorkflowService()

router = APIRouter(
    prefix="/workflow",
    tags=["workflow"],
    responses={404: {"description": "Not found"}},
)


# ── 1. 列出所有工作流 ──────────────────────────────────────────────────────────

@router.get("/list")
def list_workflows() -> List[WorkflowPO]:
    """
    列出所有工作流。

    :return: 工作流列表
    """
    return workflow_service.list_workflows()


# ── 2. 获取工作流详情 ──────────────────────────────────────────────────────────

@router.get("/get/{workflow_id}")
def get_workflow(workflow_id: str) -> WorkflowPO:
    """
    按 ID 获取工作流详情。

    :param workflow_id: 工作流 ID
    :return: 工作流对象
    """
    wf = workflow_service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"工作流 {workflow_id} 不存在")
    return wf


# ── 3. 创建工作流 ──────────────────────────────────────────────────────────────

@router.post("/create")
async def create_workflow(request: Request) -> WorkflowPO:
    """
    创建新工作流。

    请求体 JSON:
      - name: str
      - description: str (可选)
      - definition: str | dict — 工作流定义（nodes + edges），可传 JSON 字符串或对象
      - trigger_type: str (可选，默认 manual)
      - trigger_config: str | dict (可选)

    :return: 创建后的 WorkflowPO
    """
    data = await request.json()

    # 验证并规范 definition
    definition = data.get("definition", "{}")
    definition_str = _normalize_json_field(definition, "definition")
    _validate_definition(definition_str)

    trigger_config = data.get("trigger_config", "{}")
    trigger_config_str = _normalize_json_field(trigger_config, "trigger_config")

    now = datetime.now(timezone.utc).isoformat()
    wf = WorkflowPO(
        id=uuid.uuid4().hex,
        name=data.get("name", "Untitled Workflow"),
        description=data.get("description", ""),
        status=WorkflowStatus.draft,
        definition=definition_str,
        trigger_type=TriggerType(data.get("trigger_type", "manual")),
        trigger_config=trigger_config_str,
        created_at=now,
        updated_at=now,
    )
    workflow_service.add_workflow(wf)
    return wf


# ── 4. 更新工作流 ──────────────────────────────────────────────────────────────

@router.put("/update/{workflow_id}")
async def update_workflow(workflow_id: str, request: Request) -> WorkflowPO:
    """
    更新工作流。

    :param workflow_id: 工作流 ID
    :return: 更新后的 WorkflowPO
    """
    data = await request.json()

    # 如果传了 definition，验证格式
    updates: Dict[str, Any] = {}
    for key in ("name", "description", "status", "trigger_type"):
        if key in data:
            updates[key] = data[key]

    if "definition" in data:
        definition_str = _normalize_json_field(data["definition"], "definition")
        _validate_definition(definition_str)
        updates["definition"] = definition_str

    if "trigger_config" in data:
        updates["trigger_config"] = _normalize_json_field(data["trigger_config"], "trigger_config")

    updated = workflow_service.update_workflow(workflow_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"工作流 {workflow_id} 不存在")
    return updated


# ── 5. 删除工作流 ──────────────────────────────────────────────────────────────

@router.delete("/delete/{workflow_id}")
def delete_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    删除工作流。

    :param workflow_id: 工作流 ID
    :return: 删除结果
    """
    success = workflow_service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"删除工作流 {workflow_id} 失败")
    return {"success": True, "id": workflow_id}


# ── 6. 执行工作流（SSE 流式返回）────────────────────────────────────────────────

@router.post("/execute/{workflow_id}")
async def execute_workflow(workflow_id: str, request: Request) -> StreamingResponse:
    """
    执行工作流并以 SSE 事件流返回进度。

    请求体 JSON:
      - input_data: dict — 工作流输入数据

    :param workflow_id: 工作流 ID
    :return: SSE StreamingResponse
    """
    wf = workflow_service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"工作流 {workflow_id} 不存在")

    data = await request.json()
    input_data: dict = data.get("input_data", {})

    engine = WorkflowEngine(wf)

    async def event_generator():
        """包装引擎输出为 SSE 事件流"""
        async for sse_line in engine.execute(input_data):
            yield sse_line

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 7. 获取可用节点类型 ────────────────────────────────────────────────────────

@router.get("/node-types")
def get_node_types() -> List[dict]:
    """
    返回可用的节点类型定义（供前端工作流编辑器使用）。

    :return: 节点类型定义列表
    """
    return NODE_TYPE_DEFINITIONS


# ── 8. 获取工作流执行历史 ──────────────────────────────────────────────────────

@router.get("/executions/{workflow_id}")
def list_executions(workflow_id: str) -> List[WorkflowExecution]:
    """
    按工作流 ID 查询执行历史记录。

    :param workflow_id: 工作流 ID
    :return: 执行记录列表（按时间倒序）
    """
    return workflow_service.list_executions(workflow_id)


# ── 辅助函数 ───────────────────────────────────────────────────────────────────

def _normalize_json_field(value: Any, field_name: str) -> str:
    """
    将字段值规范为 JSON 字符串。

    支持传入 dict/list 或 JSON 字符串。
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        # 验证是否为合法 JSON
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} 必须是合法的 JSON 字符串或对象",
            )
    return "{}"


def _validate_definition(definition_str: str) -> None:
    """
    校验工作流 definition 的基本结构。

    要求包含 nodes (list) 和 edges (list)，每个 node 必须有 id 和 type。
    """
    try:
        defn = json.loads(definition_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="definition 不是合法的 JSON")

    if not isinstance(defn, dict):
        raise HTTPException(status_code=400, detail="definition 必须是 JSON 对象")

    nodes = defn.get("nodes")
    if not isinstance(nodes, list):
        raise HTTPException(status_code=400, detail="definition.nodes 必须是数组")

    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise HTTPException(status_code=400, detail=f"definition.nodes[{i}] 必须是对象")
        if "id" not in node:
            raise HTTPException(status_code=400, detail=f"definition.nodes[{i}] 缺少 id 字段")
        if "type" not in node:
            raise HTTPException(status_code=400, detail=f"definition.nodes[{i}] 缺少 type 字段")

    edges = defn.get("edges")
    if not isinstance(edges, list):
        raise HTTPException(status_code=400, detail="definition.edges 必须是数组")

    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise HTTPException(status_code=400, detail=f"definition.edges[{i}] 必须是对象")
        if "source" not in edge or "target" not in edge:
            raise HTTPException(
                status_code=400,
                detail=f"definition.edges[{i}] 缺少 source 或 target 字段",
            )
