# workflow/models.py — 工作流数据模型与 DynamoDB 持久化服务
"""
定义 WorkflowPO（工作流持久化对象）、WorkflowExecution（执行记录）、
WorkflowService（DynamoDB CRUD）。
"""

import boto3
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from boto3.dynamodb.conditions import Attr, Key
from pydantic import BaseModel, Field

from ..utils.aws_config import get_aws_region


# ── 枚举 ──────────────────────────────────────────────────────────────────────

class WorkflowStatus(str, Enum):
    """工作流状态"""
    draft = "draft"
    published = "published"
    archived = "archived"


class TriggerType(str, Enum):
    """工作流触发类型"""
    manual = "manual"
    schedule = "schedule"
    webhook = "webhook"


class ExecutionStatus(str, Enum):
    """执行状态"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


# ── 数据模型 ──────────────────────────────────────────────────────────────────

class WorkflowPO(BaseModel):
    """工作流持久化对象"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.draft
    definition: str = "{}"  # JSON 字符串，包含 nodes / edges
    trigger_type: TriggerType = TriggerType.manual
    trigger_config: str = "{}"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = None


class WorkflowExecution(BaseModel):
    """工作流执行记录"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    workflow_id: str = ""
    status: ExecutionStatus = ExecutionStatus.pending
    input_data: str = "{}"   # JSON 字符串
    output_data: str = "{}"  # JSON 字符串
    node_states: str = "{}"  # JSON 字符串，node_id → 状态快照
    error_message: str = ""
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    total_tokens: int = 0
    total_duration_ms: int = 0


# ── DynamoDB 服务层 ────────────────────────────────────────────────────────────

class WorkflowService:
    """
    工作流 CRUD 服务，使用 DynamoDB 存储。
    参照 AgentPOService 的 DynamoDB 操作模式。
    """

    workflow_table_name = "WorkflowTable"
    execution_table_name = "WorkflowExecutionTable"

    def __init__(self) -> None:
        aws_region = get_aws_region()
        self.dynamodb = boto3.resource("dynamodb", region_name=aws_region)

    # ── Workflow CRUD ──────────────────────────────────────────────────────

    def add_workflow(self, wf: WorkflowPO) -> WorkflowPO:
        """创建或覆盖工作流"""
        table = self.dynamodb.Table(self.workflow_table_name)
        table.put_item(Item=self._workflow_to_item(wf))
        return wf

    def get_workflow(self, wf_id: str) -> Optional[WorkflowPO]:
        """按 ID 获取工作流"""
        table = self.dynamodb.Table(self.workflow_table_name)
        response = table.get_item(Key={"id": wf_id})
        if "Item" in response:
            return self._item_to_workflow(response["Item"])
        return None

    def list_workflows(self) -> List[WorkflowPO]:
        """列出所有工作流"""
        table = self.dynamodb.Table(self.workflow_table_name)
        response = table.scan()
        items = response.get("Items", [])
        return [self._item_to_workflow(item) for item in items]

    def update_workflow(self, wf_id: str, updates: dict) -> Optional[WorkflowPO]:
        """
        部分更新工作流字段。

        :param wf_id: 工作流 ID
        :param updates: 要更新的字段字典
        :return: 更新后的 WorkflowPO，若不存在返回 None
        """
        existing = self.get_workflow(wf_id)
        if not existing:
            return None

        # 合并更新
        data = existing.model_dump()
        data.update(updates)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # 如果状态变为 published 且之前不是，记录 published_at
        if updates.get("status") == WorkflowStatus.published and existing.status != WorkflowStatus.published:
            data["published_at"] = datetime.now(timezone.utc).isoformat()

        updated_wf = WorkflowPO(**data)
        table = self.dynamodb.Table(self.workflow_table_name)
        table.put_item(Item=self._workflow_to_item(updated_wf))
        return updated_wf

    def delete_workflow(self, wf_id: str) -> bool:
        """删除工作流"""
        table = self.dynamodb.Table(self.workflow_table_name)
        response = table.delete_item(Key={"id": wf_id})
        return response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200

    # ── Execution CRUD ─────────────────────────────────────────────────────

    def add_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        """创建执行记录"""
        table = self.dynamodb.Table(self.execution_table_name)
        table.put_item(Item=self._execution_to_item(execution))
        return execution

    def update_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        """更新执行记录（全量覆盖）"""
        table = self.dynamodb.Table(self.execution_table_name)
        table.put_item(Item=self._execution_to_item(execution))
        return execution

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """按 ID 获取执行记录"""
        table = self.dynamodb.Table(self.execution_table_name)
        response = table.get_item(Key={"id": execution_id})
        if "Item" in response:
            return self._item_to_execution(response["Item"])
        return None

    def list_executions(self, workflow_id: str) -> List[WorkflowExecution]:
        """按工作流 ID 查询所有执行记录"""
        table = self.dynamodb.Table(self.execution_table_name)
        response = table.scan(
            FilterExpression=Attr("workflow_id").eq(workflow_id)
        )
        items = response.get("Items", [])
        executions = [self._item_to_execution(item) for item in items]
        return sorted(executions, key=lambda e: e.started_at, reverse=True)

    # ── 序列化 / 反序列化 ──────────────────────────────────────────────────

    @staticmethod
    def _workflow_to_item(wf: WorkflowPO) -> dict:
        """将 WorkflowPO 转为 DynamoDB Item"""
        item = {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "status": wf.status.value if isinstance(wf.status, WorkflowStatus) else wf.status,
            "definition": wf.definition,
            "trigger_type": wf.trigger_type.value if isinstance(wf.trigger_type, TriggerType) else wf.trigger_type,
            "trigger_config": wf.trigger_config,
            "created_at": wf.created_at,
            "updated_at": wf.updated_at,
        }
        if wf.published_at:
            item["published_at"] = wf.published_at
        return item

    @staticmethod
    def _item_to_workflow(item: dict) -> WorkflowPO:
        """将 DynamoDB Item 转为 WorkflowPO"""
        return WorkflowPO(
            id=item["id"],
            name=item.get("name", ""),
            description=item.get("description", ""),
            status=WorkflowStatus(item.get("status", "draft")),
            definition=item.get("definition", "{}"),
            trigger_type=TriggerType(item.get("trigger_type", "manual")),
            trigger_config=item.get("trigger_config", "{}"),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
            published_at=item.get("published_at"),
        )

    @staticmethod
    def _execution_to_item(ex: WorkflowExecution) -> dict:
        """将 WorkflowExecution 转为 DynamoDB Item"""
        item = {
            "id": ex.id,
            "workflow_id": ex.workflow_id,
            "status": ex.status.value if isinstance(ex.status, ExecutionStatus) else ex.status,
            "input_data": ex.input_data,
            "output_data": ex.output_data,
            "node_states": ex.node_states,
            "error_message": ex.error_message,
            "started_at": ex.started_at,
            "total_tokens": ex.total_tokens,
            "total_duration_ms": ex.total_duration_ms,
        }
        if ex.completed_at:
            item["completed_at"] = ex.completed_at
        return item

    @staticmethod
    def _item_to_execution(item: dict) -> WorkflowExecution:
        """将 DynamoDB Item 转为 WorkflowExecution"""
        return WorkflowExecution(
            id=item["id"],
            workflow_id=item.get("workflow_id", ""),
            status=ExecutionStatus(item.get("status", "pending")),
            input_data=item.get("input_data", "{}"),
            output_data=item.get("output_data", "{}"),
            node_states=item.get("node_states", "{}"),
            error_message=item.get("error_message", ""),
            started_at=item.get("started_at", ""),
            completed_at=item.get("completed_at"),
            total_tokens=int(item.get("total_tokens", 0)),
            total_duration_ms=int(item.get("total_duration_ms", 0)),
        )


# ── 工作流执行持久化服务（工程师 C） ──────────────────────────────────────────

class WorkflowExecutionService:
    """
    工作流执行记录的专用持久化服务。

    使用 DynamoDB ``WorkflowExecutionTable`` 及其 GSI ``workflow_id-index``
    实现高效的执行记录 CRUD 操作。
    与 WorkflowService 中的基础 CRUD 互补，本服务提供:
      - 基于 GSI 的高效查询（替代 Scan + FilterExpression）
      - 原子状态更新（update_item 替代全量 put_item）
      - 面向引擎层的简化接口
    """

    table_name = "WorkflowExecutionTable"
    gsi_name = "workflow_id-index"

    def __init__(self) -> None:
        aws_region = get_aws_region()
        self.dynamodb = boto3.resource("dynamodb", region_name=aws_region)

    # ── 写入 ──────────────────────────────────────────────────────────────

    def save_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        """
        保存（创建或覆盖）一条执行记录。

        :param execution: 要持久化的 WorkflowExecution 对象
        :return: 传入的 execution 对象（方便链式调用）
        """
        table = self.dynamodb.Table(self.table_name)
        item = self._to_item(execution)
        table.put_item(Item=item)
        return execution

    # ── 读取 ──────────────────────────────────────────────────────────────

    def get_execution(self, exec_id: str) -> Optional[WorkflowExecution]:
        """
        按主键获取单条执行记录。

        :param exec_id: 执行记录 ID
        :return: WorkflowExecution 或 None
        """
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={"id": exec_id})
        if "Item" in response:
            return self._from_item(response["Item"])
        return None

    def list_executions(
        self,
        workflow_id: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> List[WorkflowExecution]:
        """
        按工作流 ID 查询执行记录（通过 GSI ``workflow_id-index``）。

        :param workflow_id: 工作流 ID
        :param limit: 最大返回条数
        :param ascending: True = 按 started_at 升序；False（默认）= 降序
        :return: WorkflowExecution 列表，按 started_at 排序
        """
        table = self.dynamodb.Table(self.table_name)
        response = table.query(
            IndexName=self.gsi_name,
            KeyConditionExpression=Key("workflow_id").eq(workflow_id),
            ScanIndexForward=ascending,
            Limit=limit,
        )
        items = response.get("Items", [])
        return [self._from_item(item) for item in items]

    # ── 更新 ──────────────────────────────────────────────────────────────

    def update_execution_status(
        self,
        exec_id: str,
        status: ExecutionStatus,
        output: Optional[str] = None,
        error_message: Optional[str] = None,
        node_states: Optional[str] = None,
        total_tokens: Optional[int] = None,
        total_duration_ms: Optional[int] = None,
    ) -> Optional[WorkflowExecution]:
        """
        原子更新执行记录的状态及可选输出字段。

        只更新传入的非 None 字段，使用 DynamoDB ``update_item`` 保证原子性，
        避免 get-then-put 的竞态风险。

        :param exec_id: 执行记录 ID
        :param status: 新的执行状态
        :param output: JSON 字符串形式的输出数据
        :param error_message: 错误信息
        :param node_states: JSON 字符串形式的节点状态快照
        :param total_tokens: 总 token 消耗
        :param total_duration_ms: 总执行时长（毫秒）
        :return: 更新后的 WorkflowExecution，若记录不存在返回 None
        """
        table = self.dynamodb.Table(self.table_name)

        # 构建动态 UpdateExpression
        update_parts: List[str] = ["#st = :status"]
        attr_names: dict = {"#st": "status"}
        attr_values: dict = {
            ":status": status.value if isinstance(status, ExecutionStatus) else status,
        }

        # 终态自动填充 completed_at
        if status in (ExecutionStatus.completed, ExecutionStatus.failed, ExecutionStatus.cancelled):
            update_parts.append("completed_at = :completed_at")
            attr_values[":completed_at"] = datetime.now(timezone.utc).isoformat()

        if output is not None:
            update_parts.append("output_data = :output_data")
            attr_values[":output_data"] = output

        if error_message is not None:
            update_parts.append("error_message = :error_message")
            attr_values[":error_message"] = error_message

        if node_states is not None:
            update_parts.append("node_states = :node_states")
            attr_values[":node_states"] = node_states

        if total_tokens is not None:
            update_parts.append("total_tokens = :total_tokens")
            attr_values[":total_tokens"] = total_tokens

        if total_duration_ms is not None:
            update_parts.append("total_duration_ms = :total_duration_ms")
            attr_values[":total_duration_ms"] = total_duration_ms

        try:
            response = table.update_item(
                Key={"id": exec_id},
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeNames=attr_names,
                ExpressionAttributeValues=attr_values,
                ReturnValues="ALL_NEW",
            )
            return self._from_item(response.get("Attributes", {}))
        except Exception:
            # 记录不存在或其他异常
            return None

    # ── 序列化 ────────────────────────────────────────────────────────────

    @staticmethod
    def _to_item(ex: WorkflowExecution) -> dict:
        """将 WorkflowExecution 转为 DynamoDB Item"""
        item: dict = {
            "id": ex.id,
            "workflow_id": ex.workflow_id,
            "status": ex.status.value if isinstance(ex.status, ExecutionStatus) else ex.status,
            "input_data": ex.input_data,
            "output_data": ex.output_data,
            "node_states": ex.node_states,
            "error_message": ex.error_message,
            "started_at": ex.started_at,
            "total_tokens": ex.total_tokens,
            "total_duration_ms": ex.total_duration_ms,
        }
        if ex.completed_at:
            item["completed_at"] = ex.completed_at
        return item

    @staticmethod
    def _from_item(item: dict) -> WorkflowExecution:
        """将 DynamoDB Item 转为 WorkflowExecution"""
        return WorkflowExecution(
            id=item.get("id", ""),
            workflow_id=item.get("workflow_id", ""),
            status=ExecutionStatus(item.get("status", "pending")),
            input_data=item.get("input_data", "{}"),
            output_data=item.get("output_data", "{}"),
            node_states=item.get("node_states", "{}"),
            error_message=item.get("error_message", ""),
            started_at=item.get("started_at", ""),
            completed_at=item.get("completed_at"),
            total_tokens=int(item.get("total_tokens", 0)),
            total_duration_ms=int(item.get("total_duration_ms", 0)),
        )
