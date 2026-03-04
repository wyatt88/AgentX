# AgentX 2.0 — 统一权威设计文档

> **版本**: v1.0 | **日期**: 2026-03-04 | **状态**: 最终定稿  
> **工程师只看这一份文档即可开始编码。**

---

## 一、产品愿景与定位

### 1.1 一句话定义

**AgentX 2.0 是一个以 Strands SDK 为 Agent 运行时、以可视化工作流为编排引擎、以 MCP 协议为工具集成层的 AI 自动化平台。**

### 1.2 竞品差异化

| 维度 | AgentX 2.0 | Dify | n8n | MCPHub |
|------|-----------|------|-----|--------|
| **Agent 运行时** | Strands SDK（AWS 原生，Agent Loop 内置） | 自研 Agent 引擎 | LangChain 集成 | 无（工具层） |
| **工作流** | Agent-First DAG（Agent 即节点） | AI Chatflow/Workflow | 通用 500+ 集成 | 无 |
| **MCP 管理** | 内置 Hub（分组 + 健康检查 + 语义路由） | 插件式 MCP Client | 无原生 MCP | 核心能力 |
| **部署目标** | AWS 原生（ECS/DynamoDB/Bedrock） | Docker Compose | Docker/Cloud | Docker |
| **核心用户** | AI 工程师 + 平台团队 | AI 应用开发者 | 运维/自动化团队 | 工具管理者 |

**设计理念**：
- 从 **Dify** 借鉴：模型网关统一切换 + RAG Pipeline + 应用一键发布
- 从 **n8n** 借鉴：可视化拖拽画布 + 节点即代码 + 条件分支
- 从 **MCPHub** 借鉴：MCP 分组管理 + 智能语义路由 + 热更新
- 从 **Strands SDK** 坚守：Agent Loop 模型驱动 + Agent-as-Tool 编排 + 流式事件

**AgentX 的独特价值**：不是另一个 Dify 或 n8n 克隆，而是 **"Strands-Native Agent Orchestration"** — 让 Strands Agent 既能独立对话，又能被编排成工作流节点，同时共享统一的 MCP 工具池和知识库。

### 1.3 核心理念

1. **Agent = LLM + Prompt + Tools + Environment** — Strands SDK 哲学
2. **增量演进，不推倒重来** — 在现有代码基础上迭代
3. **MVP 务实** — P0 功能 5 个工程师 3 小时能交付
4. **标准化** — MCP 协议统一工具生态，RESTful API 统一接口

---

## 二、系统架构

### 2.1 架构演进路线

#### 1.0 — 现有架构（已实现）

```
┌─────────────────── 用户层 ───────────────────┐
│  React 前端 (Ant Design)  │  API 客户端      │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 应用层 ───────────────────┐
│           FastAPI 后端（单体）                │
│  ┌─────────┬──────────┬──────────┬─────────┐ │
│  │ Agent   │   MCP    │  Chat    │Schedule │ │
│  │ CRUD    │  CRUD    │  对话    │ 调度    │ │
│  └─────────┴──────────┴──────────┴─────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 数据层 ───────────────────┐
│  DynamoDB: AgentTable | ChatRecordTable |    │
│  HttpMCPTable | AgentScheduleTable           │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 工具层 ───────────────────┐
│  Strands 内置工具 | MCP Servers | Agent-as-Tool │
└─────────────────────────────────────────────┘
```

**已有能力**：Agent CRUD + SSE 流式对话 + MCP 管理（含分组/健康检查/工具发现）+ 定时调度 + 基础工作流引擎 + 模型 Provider 管理

#### 2.0 — MVP 目标架构（本次交付）

```
┌─────────────────────────────────────────────────────────┐
│                    展示层 (React + Ant Design)            │
│  Agent 管理 | 工作流画布 | MCP Hub | 模型管理 | 对话 | 调度│
├─────────────────────────────────────────────────────────┤
│                    API 层 (FastAPI 单体)                  │
│  RESTful API + SSE 流式                                  │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Agent   │ Workflow │   MCP    │  Model   │  Schedule   │
│  Engine  │  Engine  │   Hub    │ Provider │  Service    │
│ (Strands)│ (DAG执行)│(工具管理) │ (多模型) │  (调度)     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    存储层                                 │
│  DynamoDB (所有元数据 + 执行记录)                          │
└─────────────────────────────────────────────────────────┘
```

**2.0 关键变化**：
- 前端新增：**工作流画布**（ReactFlow）+ **模型管理页面** + 增强的 MCP Hub
- 后端新增：**工作流引擎**（DAG 执行）+ **模型 Provider 管理** + MCP 健康检查
- 保持单体架构，不做微服务拆分

#### 3.0 — 愿景架构（未来 1-3 月）

```
┌─────────────────────────────────────────────────────────┐
│  管理控制台 | 工作流编辑器 | 应用发布页面 | 监控仪表盘    │
├─────────────────────────────────────────────────────────┤
│                统一 API 网关 (Kong/ALB)                   │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Agent   │ Workflow │   MCP    │Knowledge │ Model       │
│  Engine  │  Engine  │   Hub    │ (RAG)    │ Gateway     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│ DynamoDB | PostgreSQL+pgvector | S3 | Redis(可选)       │
├─────────────────────────────────────────────────────────┤
│ 可观测性: CloudWatch + Traces | 应用发布: API/Bot/Web    │
└─────────────────────────────────────────────────────────┘
```

**3.0 新增**：RAG/知识库（pgvector）、模型网关（智能路由）、应用发布、可观测性、RBAC

### 2.2 架构决策记录

| 决策 | 统一结论 | 理由 |
|------|---------|------|
| **数据库** | DynamoDB（全量），P1 再引入 PostgreSQL | 2.0 MVP 不引入新存储依赖，现有 DynamoDB 够用 |
| **向量数据库** | P1 用 PostgreSQL + pgvector（非 OpenSearch） | pgvector 轻量、与 PG 复用，万级文档足够 |
| **缓存** | P0 不引入 Redis | 单体架构 + DynamoDB 延迟够低 |
| **后端架构** | 保持 FastAPI 单体 | 5 人团队不需要微服务开销 |
| **消息队列** | P0 不引入 SQS | 工作流同步执行 + SSE 推送足够 |
| **工作流画布** | ReactFlow (@xyflow/react) | React 生态最成熟的 DAG 库，Dify/n8n 同类方案 |
| **状态管理** | Zustand（保持） | 已有，轻量够用 |
| **部署** | ECS Fargate（保持） | 现有 CI/CD，不折腾 |

---

## 三、功能模块总览

### P0 — 必须实现（3 小时 MVP Sprint）

> 原则：在**现有代码基础上增量开发**，最大限度复用已有模块。

#### 3.1 工作流引擎（核心新功能）

**功能描述**：可视化 DAG 工作流编辑器 + 后端执行引擎，支持将 Agent 编排成自动化流程。

**核心用户故事**：
- 作为 AI 工程师，我想在画布上拖拽创建工作流，把多个 Agent 串联起来
- 作为 AI 工程师，我想一键执行工作流，并实时看到每个节点的执行状态
- 作为 AI 工程师，我想保存工作流后刷新页面仍能恢复

**技术方案概要**：
- 前端：ReactFlow 画布 + 5 种自定义节点（Start/Agent/Condition/Code/End）
- 后端：BFS DAG 遍历引擎 + SSE 事件流
- 存储：DynamoDB `WorkflowTable` + `WorkflowExecutionTable`
- **现有代码**：`be/app/workflow/` 已实现完整引擎，`fe/src/components/workflow/` 已有组件骨架

**依赖关系**：依赖 Agent 模块（Agent 节点调用 `AgentPOService.stream_chat()`）

#### 3.2 MCP Hub 增强

**功能描述**：在现有 MCP CRUD 基础上，增加分组管理、健康检查状态展示、工具列表查看。

**核心用户故事**：
- 作为平台管理员，我想一键检测所有 MCP Server 的连通性
- 作为 AI 工程师，我想按分组筛选 MCP Server
- 作为 AI 工程师，我想查看某个 MCP Server 暴露的工具列表

**技术方案概要**：
- 前端：表格新增分组/状态/工具数列 + 健康检查按钮 + 工具列表 Modal
- 后端：MCPClient 连接检测 + 工具发现
- **现有代码**：`be/app/mcp/mcp.py` 已实现分组/健康检查/工具发现，`fe/src/components/mcp/MCP.tsx` 需增强 UI

**依赖关系**：无外部依赖

#### 3.3 模型管理

**功能描述**：将模型 Provider 配置从 Agent 表单中抽离为独立管理模块。

**核心用户故事**：
- 作为平台管理员，我想统一管理多个模型 Provider（Bedrock/OpenAI/Ollama）
- 作为平台管理员，我想测试 Provider 的连通性
- 作为 AI 工程师，创建 Agent 时能从所有 active Provider 中选择模型

**技术方案概要**：
- 前端：Provider 列表页 + 创建/编辑 Modal + 连通性测试
- 后端：DynamoDB `ModelProviderTable` CRUD + 类型化测试逻辑
- **现有代码**：`be/app/model/` 已完整实现，`fe/src/components/model/ModelProvider.tsx` 已有

**依赖关系**：Agent 模块的 `_build_model()` 已集成 ModelProviderTable 查询

#### 3.4 前端路由 & 导航更新

**功能描述**：更新侧边栏导航和路由，接入工作流和模型管理页面。

**现有代码**：`fe/src/components/layout/Layout.tsx` 当前仅有 4 个路由（chat/agent/mcp/schedule），需新增 workflows 和 models 路由。


### P1 — 重要功能（后续 1-2 周迭代）

| 模块 | 功能 | 技术方案 | 依赖 |
|------|------|---------|------|
| **知识库 (RAG)** | 文档上传 + 分块 + 向量检索 | PostgreSQL + pgvector + Bedrock Embedding | S3（文件存储）|
| **工作流高级节点** | Loop / Parallel / HTTP / LLM 节点 | 扩展 `nodes.py` 执行器注册表 | 工作流引擎 |
| **MCP 智能路由** | 语义搜索匹配最佳工具 | pgvector + Embedding + MCPHub 模式 | pgvector |
| **应用发布** | Agent/Workflow 一键发布为 API | 生成独立 API endpoint + API Key 认证 | Agent + Workflow |
| **可观测性 MVP** | Token 消耗统计 + 调用延迟追踪 | DynamoDB 持久化 + 前端仪表盘 | Agent + Workflow |
| **Human-in-the-Loop** | 工作流暂停等待人工确认后恢复 | 执行记录 paused 状态 + WebSocket 通知 | 工作流引擎 |
| **工作流版本管理** | Draft / Published 状态 + 版本历史 | definition 快照 + 版本号字段 | 工作流引擎 |

### P2 — 未来规划（1-3 月）

| 模块 | 功能 | 说明 |
|------|------|------|
| **Marketplace** | 工作流/Agent 模板市场 | 社区共享 + 模板导入导出 |
| **Multi-Agent** | Swarm / Graph 多 Agent 协作 | Strands SDK 原生支持 |
| **RAG 2.0** | 混合检索策略 + 自定义 Pipeline | BM25 + 向量 + 重排序 |
| **WebApp 发布** | 一键生成独立 Chatbot 页面 | React 模板 + 动态路由 |
| **RBAC** | 角色权限管理 | JWT + 权限矩阵 |
| **API Key 轮转** | 模型 API Key 负载均衡 | 多 Key 轮转 + 健康监测 |
| **导入导出** | 工作流 YAML/JSON 导入导出 | 标准化格式定义 |
| **微服务拆分** | 按模块拆分为独立服务 | Kong 网关 + EKS |

---

## 四、数据模型设计

> **统一决策**：全部使用 DynamoDB。两份文档的字段差异已消除。

### 4.1 现有表（保留，已增强）

#### AgentTable

| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| `id` | String (PK) | UUID | 现有 |
| `name` | String | 英文标识符 | 现有 |
| `display_name` | String | 显示名称 | 现有 |
| `description` | String | 描述 | 现有 |
| `agent_type` | Number | 1=plain, 2=orchestrator | 现有 |
| `model_provider` | Number | 1=bedrock, 2=openai, ... | 现有 |
| `model_id` | String | 模型标识 | 现有 |
| `sys_prompt` | String | 系统提示词 | 现有 |
| `tools` | List[JSON] | 工具列表（AgentTool 序列化） | 现有 |
| `envs` | String | 环境变量（KEY=VALUE 换行分隔） | 现有 |
| `extras` | Map | 扩展字段(base_url, api_key 等) | 现有 |
| `created_at` | String | 创建时间 ISO-8601 | **已新增** |
| `updated_at` | String | 更新时间 ISO-8601 | **已新增** |

> **注意**：`agent_type` 和 `model_provider` 在代码中使用 Enum 映射，前端用数字传递。

#### HttpMCPTable

| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| `id` | String (PK) | UUID | 现有 |
| `name` | String | Server 名称 | 现有 |
| `desc` | String | 描述 | 现有 |
| `host` | String | Streamable HTTP URL | 现有 |
| `group` | String | 分组名称（默认 "default"） | **已新增** |
| `status` | String | "unknown" / "running" / "error" | **已新增** |
| `health_check_at` | String | 上次健康检查时间 | **已新增** |
| `tools_count` | Number | 工具数量（缓存） | **已新增** |
| `tags` | List[String] | 标签 | **已新增** |

#### ChatRecordTable / ChatResponseTable / AgentScheduleTable

保持现有结构不变。

### 4.2 新增表

#### WorkflowTable

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String (PK) | UUID |
| `name` | String | 工作流名称 |
| `description` | String | 描述 |
| `status` | String | "draft" / "published" / "archived" |
| `definition` | String | JSON 序列化的 DAG 定义（nodes + edges） |
| `trigger_type` | String | "manual" / "schedule" / "webhook" |
| `trigger_config` | String | 触发配置 JSON |
| `created_at` | String | 创建时间 |
| `updated_at` | String | 更新时间 |
| `published_at` | String | 最近发布时间（可选） |

**definition JSON 结构**：
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "start",
      "position": {"x": 100, "y": 200},
      "data": {},
      "config": {}
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "node_1",
      "target": "node_2",
      "label": ""
    }
  ]
}
```

#### WorkflowExecutionTable

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String (PK) | 执行 ID |
| `workflow_id` | String (GSI) | 工作流 ID |
| `status` | String | "pending" / "running" / "completed" / "failed" / "cancelled" |
| `input_data` | String | 输入数据 JSON |
| `output_data` | String | 输出数据 JSON |
| `node_states` | String | 各节点执行状态快照 JSON |
| `error_message` | String | 错误信息 |
| `started_at` | String | 开始时间（GSI Sort Key） |
| `completed_at` | String | 完成时间 |
| `total_tokens` | Number | Token 消耗总计 |
| `total_duration_ms` | Number | 总耗时（毫秒） |

**GSI**: `workflow_id-index` (PK=workflow_id, SK=started_at)

#### ModelProviderTable

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String (PK) | UUID |
| `name` | String | 显示名称 |
| `type` | String | "bedrock" / "openai" / "ollama" / "anthropic" / "custom" |
| `config` | Map | 配置信息（region/base_url/api_key 等） |
| `models` | List[String] | 可用模型列表 |
| `is_default` | Boolean | 是否默认 Provider |
| `status` | String | "active" / "inactive" / "error" / "unknown" |
| `created_at` | String | 创建时间 |
| `updated_at` | String | 更新时间 |

### 4.3 DynamoDB 表总览

| 表名 | PK | GSI | 状态 |
|------|-----|-----|------|
| AgentTable | id | — | 现有（已增强） |
| HttpMCPTable | id | — | 现有（已增强） |
| AgentScheduleTable | id | — | 现有 |
| ChatRecordTable | id | — | 现有 |
| ChatResponseTable | id + resp_no | — | 现有 |
| **WorkflowTable** | id | — | 🆕 已实现 |
| **WorkflowExecutionTable** | id | workflow_id-index | 🆕 已实现 |
| **ModelProviderTable** | id | — | 🆕 已实现 |

---

## 五、API 设计

### 5.1 现有 API（保留不变）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/agent/list` | Agent 列表 | ✅ 现有 |
| GET | `/api/agent/get/{id}` | 获取 Agent | ✅ 现有 |
| POST | `/api/agent/createOrUpdate` | 创建/更新 Agent | ✅ 现有 |
| DELETE | `/api/agent/delete/{id}` | 删除 Agent | ✅ 现有 |
| POST | `/api/agent/stream_chat` | 流式对话 (SSE) | ✅ 现有 |
| GET | `/api/agent/tool_list` | 可用工具列表（含 MCP group/status 信息） | ✅ 已增强 |
| GET | `/api/mcp/list` | MCP Server 列表 | ✅ 现有 |
| POST | `/api/mcp/createOrUpdate` | 创建/更新 MCP Server | ✅ 现有 |
| DELETE | `/api/mcp/delete/{id}` | 删除 MCP Server | ✅ 现有 |
| GET | `/api/chat/list_record` | 对话记录列表 | ✅ 现有 |
| GET | `/api/chat/list_chat_responses` | 对话响应列表 | ✅ 现有 |
| DELETE | `/api/chat/del_chat` | 删除对话 | ✅ 现有 |
| GET | `/api/schedule/list` | 调度任务列表 | ✅ 现有 |
| POST | `/api/schedule/create` | 创建调度 | ✅ 现有 |
| PUT | `/api/schedule/update/{id}` | 更新调度 | ✅ 现有 |
| DELETE | `/api/schedule/delete/{id}` | 删除调度 | ✅ 现有 |

### 5.2 新增 API — 工作流（已实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workflow/list` | 工作流列表 |
| GET | `/api/workflow/get/{id}` | 获取工作流详情 |
| POST | `/api/workflow/create` | 创建工作流 |
| PUT | `/api/workflow/update/{id}` | 更新工作流 |
| DELETE | `/api/workflow/delete/{id}` | 删除工作流 |
| POST | `/api/workflow/execute/{id}` | 执行工作流（SSE 流式返回） |
| GET | `/api/workflow/node-types` | 可用节点类型列表 |
| GET | `/api/workflow/executions/{wf_id}` | 工作流执行历史 |

### 5.3 新增 API — MCP Hub 增强（已实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/mcp/groups` | MCP 分组列表 |
| PUT | `/api/mcp/update/{id}` | 更新 MCP Server（group, tags） |
| POST | `/api/mcp/health-check/{id}` | 单个 Server 健康检查 |
| POST | `/api/mcp/health-check-all` | 全部 Server 健康检查 |
| GET | `/api/mcp/tools/{server_id}` | 获取某 Server 的工具列表 |

### 5.4 新增 API — 模型管理（已实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/model/providers` | Provider 列表 |
| GET | `/api/model/provider/{id}` | Provider 详情 |
| POST | `/api/model/provider` | 创建 Provider |
| PUT | `/api/model/provider/{id}` | 更新 Provider |
| DELETE | `/api/model/provider/{id}` | 删除 Provider |
| POST | `/api/model/provider/{id}/test` | 测试 Provider 连通性 |
| GET | `/api/model/available-models` | 所有可用模型（聚合 active Provider） |

### 5.5 关键 API 详细设计

#### POST /api/workflow/create

```json
// Request
{
  "name": "数据分析工作流",
  "description": "自动分析销售数据并生成报告",
  "definition": {
    "nodes": [
      {"id": "n1", "type": "start", "position": {"x": 100, "y": 200}, "data": {}},
      {"id": "n2", "type": "agent", "position": {"x": 300, "y": 200}, "data": {"agent_id": "xxx"}},
      {"id": "n3", "type": "end", "position": {"x": 500, "y": 200}, "data": {}}
    ],
    "edges": [
      {"id": "e1", "source": "n1", "target": "n2"},
      {"id": "e2", "source": "n2", "target": "n3"}
    ]
  }
}

// Response
{
  "id": "abc123",
  "name": "数据分析工作流",
  "status": "draft",
  "definition": "...",
  "created_at": "2026-03-04T19:00:00Z",
  "updated_at": "2026-03-04T19:00:00Z"
}
```

#### POST /api/workflow/execute/{id}

```json
// Request
{
  "input_data": {
    "user_message": "分析一下今天的销售数据"
  }
}

// Response (SSE stream)
data: {"event":"workflow_start","execution_id":"exec_1","workflow_id":"abc123","workflow_name":"数据分析工作流"}

data: {"event":"node_start","execution_id":"exec_1","node_id":"n1","node_type":"start"}

data: {"event":"node_complete","execution_id":"exec_1","node_id":"n1","output":{"user_message":"分析一下今天的销售数据"},"duration_ms":1}

data: {"event":"node_start","execution_id":"exec_1","node_id":"n2","node_type":"agent"}

data: {"event":"node_complete","execution_id":"exec_1","node_id":"n2","output":{"response":"根据分析...","agent_id":"xxx","total_tokens":1200},"duration_ms":3500}

data: {"event":"workflow_complete","execution_id":"exec_1","total_duration_ms":5000,"total_tokens":1200}
```

#### POST /api/mcp/health-check/{id}

```json
// Response (Success)
{
  "status": "running",
  "tools": [
    {"name": "query_database", "description": "Execute SQL query"},
    {"name": "list_tables", "description": "List all tables"}
  ],
  "tools_count": 2
}

// Response (Failure)
{
  "status": "error",
  "error": "Connection refused: http://mcp-server:8000"
}
```

#### POST /api/model/provider

```json
// Request
{
  "name": "My OpenAI",
  "type": "openai",
  "config": {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-xxx"
  },
  "models": ["gpt-4o", "gpt-4-turbo"],
  "is_default": false
}

// Response
{
  "id": "prov_123",
  "name": "My OpenAI",
  "type": "openai",
  "status": "unknown",
  "created_at": "2026-03-04T19:00:00Z"
}
```

---

## 六、前端页面设计

### 6.1 路由规划

```
/ (根路由 → 重定向 /chat)
├── /chat                    # Agent 对话（现有）
├── /agent                   # Agent 管理（现有）
├── /workflows               # 🆕 工作流列表
│   └── /workflows/:id       # 🆕 工作流画布编辑
├── /mcp                     # MCP Hub（现有 → 增强）
├── /models                  # 🆕 模型管理
├── /schedule                # 调度管理（现有）
├── /knowledge               # 知识库（P1）
├── /monitor                 # 监控面板（P1）
└── /apps                    # 应用发布（P1）
```

### 6.2 侧边栏导航更新

```
📋 Agent X 2.0
├── 💬 对话           → /chat          (现有)
├── 🤖 Agents        → /agent         (现有)
├── 🔀 工作流         → /workflows     (🆕)
├── 🔧 MCP Hub       → /mcp           (增强)
├── 🧠 模型管理       → /models        (🆕)
├── ⏰ 调度           → /schedule      (现有)
├── 📚 知识库         → /knowledge     (P1, 灰色)
└── 📊 监控           → /monitor       (P1, 灰色)
```

**文件变更**: `fe/src/components/layout/Layout.tsx`
- 导入 WorkflowList, WorkflowCanvas, ModelProvider 组件
- 新增 menuItems 条目和 Routes

### 6.3 P0 阶段页面清单（8 个页面）

| 页面 | 路由 | 改动类型 | 优先级 |
|------|------|---------|--------|
| Agent 对话 | /chat | 无改动 | — |
| Agent 管理 | /agent | 无改动 | — |
| **工作流列表** | /workflows | 🆕 新建 | P0 |
| **工作流画布** | /workflows/:id | 🆕 新建 | P0 |
| **MCP Hub** | /mcp | 增强 | P0 |
| **模型管理** | /models | 🆕 新建 | P0 |
| 调度管理 | /schedule | 无改动 | — |
| 路由/导航 | Layout.tsx | 更新 | P0 |

### 6.4 工作流画布页面详细设计

**三栏布局**：
```
┌──────────┬─────────────────────────────────────┬──────────────┐
│          │        顶部工具栏                      │              │
│  节点面板 │  [← 返回] [工作流名称] [保存] [发布] [执行] │  属性面板     │
│  (200px) │                                      │  (300px)     │
│          ├─────────────────────────────────────┤              │
│ ▶ Start  │                                      │ 选中节点的    │
│ 🤖 Agent │       ReactFlow 画布区域              │ 配置表单      │
│ ⚡ 条件   │       （拖拽 + 连线 + 缩放）          │              │
│ </> 代码  │                                      │ Agent ID     │
│ ⏹ End    │                                      │ 表达式       │
│          │       [Background] [Controls] [MiniMap]│ 代码         │
└──────────┴─────────────────────────────────────┴──────────────┘
```

**交互流程**：
1. 从左侧 NodePanel 拖拽节点到画布 → `onDrop` 添加节点
2. 点击节点 → 右侧 PropertyPanel 显示配置表单
3. 从节点 Handle 拖拽到另一节点 → `onConnect` 创建边
4. 点击保存 → 收集 nodes + edges → `PUT /api/workflow/update/{id}`
5. 点击执行 → `POST /api/workflow/execute/{id}` → SSE 实时显示节点状态

**节点组件规范**：

| 节点类型 | 颜色 | 图标 | Handles |
|---------|------|------|---------|
| Start | #52c41a (绿) | ▶ PlayCircle | 1 输出 |
| Agent | #1890ff (蓝) | 🤖 Robot | 1 输入 + 1 输出 |
| Condition | #faad14 (黄) | ⚡ Branch | 1 输入 + 2 输出 (true/false) |
| Code | #722ed1 (紫) | </> Code | 1 输入 + 1 输出 |
| End | #ff4d4f (红) | ⏹ Stop | 1 输入 |

### 6.5 MCP Hub 页面增强

在现有 `MCP.tsx` 基础上增加：
- **分组筛选下拉框**（顶部）
- **表格新增列**：分组(Tag)、状态(Badge: running=绿/error=红/unknown=灰)、工具数
- **操作增强**：每行 "健康检查" 按钮 + 点击工具数弹出工具列表 Modal
- **顶部按钮**："全部检查" 按钮
- **创建/编辑 Modal 增加字段**：group(Select)、tags(Select mode=tags)

### 6.6 模型管理页面

- Ant Design Table 列表：名称、类型(Tag)、可用模型数、状态(Badge)、操作
- 创建/编辑 Modal：
  - 类型选择(Select): bedrock / openai / ollama / anthropic / custom
  - 根据类型动态显示配置：bedrock→Region / openai→Base URL+API Key / ollama→Base URL
  - 可用模型列表(Select mode=tags)
  - 是否默认(Switch)
- "测试连接" 按钮 → `POST /api/model/provider/{id}/test`

---

## 七、技术选型

### 7.1 统一技术栈

| 层级 | 技术 | 版本 | 理由 |
|------|------|------|------|
| **前端框架** | React + TypeScript | 18.x | 现有，团队熟悉 |
| **UI 组件库** | Ant Design | 5.x | 现有，企业级组件完备 |
| **工作流画布** | @xyflow/react (ReactFlow) | 12.x | React 生态最成熟的 DAG 编辑库，MIT 协议 |
| **前端状态** | Zustand | 4.x | 现有，轻量高效 |
| **HTTP 客户端** | Axios | 1.x | 现有 |
| **后端框架** | FastAPI | 0.100+ | 现有，原生异步 + 自动 OpenAPI 文档 |
| **Agent 运行时** | Strands Agents SDK | Latest | 核心，AWS 原生 Agent Loop |
| **MCP 协议** | mcp-python + Streamable HTTP | Latest | 现有，标准化工具接口 |
| **数据库** | DynamoDB | — | 现有，无服务器免运维 |
| **部署** | ECS Fargate + ECR | — | 现有 CI/CD 流水线 |
| **前端构建** | Vite | 5.x | 现有，快速 HMR |
| **包管理** | npm (前端) + pip (后端) | — | 现有 |

### 7.2 P1 新增技术

| 技术 | 用途 | 引入时机 |
|------|------|---------|
| PostgreSQL + pgvector | 向量存储 + 知识库检索 | P1 知识库 |
| S3 | 文档原文件存储 | P1 知识库 |
| Bedrock Embedding | 文档/工具向量化 | P1 知识库 + MCP 智能路由 |

### 7.3 明确不引入的技术（2.0 MVP 阶段）

| 技术 | 不引入理由 |
|------|-----------|
| Redis | DynamoDB 延迟够低，无缓存需求 |
| SQS/SNS | 工作流同步执行 + SSE 推送足够 |
| Kong API Gateway | 单体架构不需要 API 网关 |
| OpenSearch | pgvector 在 P1 阶段够用，不需要独立向量库 |
| Terraform/CDK | 3 张 DynamoDB 表手动建即可 |
| Monaco Editor | P0 用 Ant Design TextArea，P1 再考虑 |

---

## 八、开发任务拆解（3 小时 Sprint）

### 8.0 总体时间分配

| 阶段 | 时间 | 内容 |
|------|------|------|
| 0:00 - 0:15 | 15 min | 全员阅读本文档 §八，确认理解，环境准备 |
| 0:15 - 2:30 | 135 min | 5 人并行开发 |
| 2:30 - 2:50 | 20 min | 集成联调 |
| 2:50 - 3:00 | 10 min | 冒烟测试 + Demo |

### 8.1 当前代码现状

> **重要**：以下模块已有完整后端实现，Sprint 重点是**前端页面完善 + 路由接入 + 联调**。

| 模块 | 后端状态 | 前端状态 | Sprint 重点 |
|------|---------|---------|------------|
| 工作流引擎 | ✅ 完整（models + engine + nodes + router） | ⚠️ 有组件骨架，需验证接入 | 前端画布完善 + 联调 |
| MCP 增强 | ✅ 完整（分组/健康检查/工具发现） | ⚠️ 有 Store，页面需增强 | MCP 页面增强 |
| 模型管理 | ✅ 完整（models + service + router） | ⚠️ 有组件骨架 | 模型页面完善 + 联调 |
| 路由导航 | — | ❌ 未接入新页面 | Layout.tsx 更新 |

### 8.2 后端工程师 A — 工作流引擎验证 + DynamoDB 建表

**职责**: 确保后端工作流完整可用，建表脚本，API 测试

#### 任务清单 (2h15m)

**1. DynamoDB 建表 (15 min)**
- 创建文件: `be/scripts/create_tables.py`
- 创建 3 张表: `WorkflowTable`、`WorkflowExecutionTable`（含 GSI）、`ModelProviderTable`
- 参考现有表结构，使用 boto3 create_table API
```python
# WorkflowExecutionTable GSI 定义
GlobalSecondaryIndexes=[{
    'IndexName': 'workflow_id-index',
    'KeySchema': [
        {'AttributeName': 'workflow_id', 'KeyType': 'HASH'},
        {'AttributeName': 'started_at', 'KeyType': 'RANGE'}
    ],
    'Projection': {'ProjectionType': 'ALL'},
    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
}]
```

**2. 工作流 API 端到端验证 (30 min)**
- 文件: `be/tests/test_workflow_e2e.py`
- 用 httpx/requests 测试完整流程:
  - `POST /workflow/create` → 创建包含 Start→Agent→End 的工作流
  - `GET /workflow/list` → 验证列表包含新工作流
  - `GET /workflow/get/{id}` → 验证 definition 完整
  - `PUT /workflow/update/{id}` → 修改 name
  - `POST /workflow/execute/{id}` → 验证 SSE 事件流
  - `GET /workflow/executions/{id}` → 验证执行历史
  - `DELETE /workflow/delete/{id}` → 验证删除

**3. 验证前端 API 路径对齐 (20 min)**
- 检查 `fe/src/services/api.ts` 中 WORKFLOW_API 路径与后端 router 路径是否一致
- **已知不一致问题**（需修复）：
  - 前端 `WORKFLOW_API.get` = `/workflow/{id}` → 后端 = `/workflow/get/{id}`
  - 前端 `WORKFLOW_API.update` = `/workflow/{id}` → 后端 = `/workflow/update/{id}`
  - 前端 `WORKFLOW_API.delete` = `/workflow/{id}` → 后端 = `/workflow/delete/{id}`
  - 前端 `WORKFLOW_API.execute` = `/workflow/{id}/execute` → 后端 = `/workflow/execute/{id}`
  - 前端 `MODEL_API.list` = `/model/provider/list` → 后端 = `/model/providers`
  - 前端 `MODEL_API.create` = `/model/provider/create` → 后端 = `/model/provider` (POST)
- **决策**: 修改 `fe/src/services/api.ts` 使之与后端路径对齐

**4. 验证 MCP 增强 API (20 min)**
- 用 httpx 测试 MCP 增强接口:
  - `POST /mcp/health-check/{id}` → 验证返回 status + tools
  - `POST /mcp/health-check-all` → 验证批量检查
  - `GET /mcp/tools/{id}` → 验证工具列表
  - `GET /mcp/groups` → 验证分组聚合

**5. 验证模型管理 API (20 min)**
- 用 httpx 测试 Model Provider 接口:
  - `POST /model/provider` → 创建 Bedrock Provider
  - `GET /model/providers` → 验证列表
  - `POST /model/provider/{id}/test` → 测试连通性
  - `GET /model/available-models` → 验证模型聚合

**6. 修复发现的 Bug (30 min 缓冲)**

**交付物**: 建表脚本 + 全 API 端到端测试通过 + Bug 修复

---

### 8.3 后端工程师 B — Agent 模块增强 + 工作流节点测试

**职责**: Agent 模块与 ModelProvider 集成验证，工作流节点执行器测试

#### 任务清单 (2h15m)

**1. 验证 Agent + ModelProvider 集成 (30 min)**
- 文件: `be/app/agent/agent.py`
- 验证 `_build_model()` 方法正确查询 ModelProviderTable
- 测试场景:
  - 创建 OpenAI Provider → 创建使用该 Provider 的 Agent → stream_chat 验证模型调用
  - ModelProviderTable 不存在时的降级行为

**2. 验证工作流节点执行器 (40 min)**
- 文件: `be/tests/test_nodes.py`
- 测试每种节点:
  - `StartNodeExecutor` — 透传 input_data
  - `AgentNodeExecutor` — mock AgentPOService，验证 stream_chat 调用和响应收集
  - `ConditionNodeExecutor` — 测试表达式 eval（true/false 分支）
  - `CodeNodeExecutor` — 测试自定义代码执行和 result 返回
  - `EndNodeExecutor` — 测试输出收集

**3. 验证工作流引擎 DAG 遍历 (30 min)**
- 文件: `be/tests/test_engine.py`
- 测试:
  - 线性工作流: Start → Agent → End
  - 条件分支: Start → Condition → (true: Code, false: End)
  - 无 start 节点时的 fallback 行为

**4. Agent 工具列表增强验证 (20 min)**
- 验证 `get_all_available_tools()`:
  - MCP 工具包含 group 和 status 信息
  - 只返回 running 状态的 MCP Server 工具

**5. 编写集成测试脚本 (30 min)**
- 文件: `be/tests/test_integration.py`
- 完整场景: 创建 Provider → 创建 Agent → 创建 Workflow(含该 Agent 节点) → 执行 → 验证

**交付物**: Agent-Model 集成验证 + 节点/引擎单元测试 + 集成测试

---

### 8.4 后端工程师 C — CORS 配置 + 建表验证 + 文档/工具支持

**职责**: 全局配置、建表验证、为前端提供 Mock 数据支持

#### 任务清单 (2h15m)

**1. CORS 中间件配置 (15 min)**
- 文件: `be/app/main.py`
- 新增:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境，生产环境限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. 全局异常处理 (15 min)**
- 文件: `be/app/main.py`
- 新增全局异常处理器:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})
```

**3. 运行建表脚本 + 验证 (20 min)**
- 运行后端工程师 A 的 `be/scripts/create_tables.py`
- 在 AWS Console 验证 3 张新表创建成功
- 验证 GSI `workflow_id-index` 存在

**4. Seed 数据脚本 (30 min)**
- 文件: `be/scripts/seed_data.py`
- 创建:
  - 1 个 Bedrock ModelProvider（is_default=True）
  - 1 个 OpenAI ModelProvider
  - 1 个示例工作流（Start → Agent → End）
  - 确保前端有数据可展示

**5. API 文档检查 (20 min)**
- 启动 FastAPI → 访问 `/docs`
- 验证所有新增路由在 Swagger UI 中正确显示
- 检查请求/响应 schema 是否完整

**6. 前端代理配置验证 (15 min)**
- 文件: `fe/vite.config.ts`
- 确保开发代理配置指向正确的后端地址:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

**7. 生产环境部署清单 (20 min)**
- 文件: `be/scripts/deploy_checklist.md`
- 记录: DynamoDB 表创建 → ECR 推送 → ECS 任务更新 → 前端构建部署

**交付物**: CORS 配置 + 建表验证 + Seed 数据 + 部署清单

---

### 8.5 前端工程师 A — 工作流画布（核心新功能）

**职责**: ReactFlow 工作流编辑器完善 + 节点组件 + 工作流列表

#### 任务清单 (2h15m)

**1. 安装 ReactFlow (5 min)**
- 命令: `cd fe && npm install @xyflow/react`

**2. 完善工作流列表页 (25 min)**
- 文件: `fe/src/components/workflow/WorkflowList.tsx`
- 内容:
  - Ant Design Card 列表（参考现有 Agent 列表风格）
  - 每 Card: 名称、描述、状态 Badge、节点数、最后更新
  - 操作: 编辑(跳转画布)、执行、删除
  - 右上角 "新建工作流" → Modal → 创建后跳转画布
  - 调用 `workflowAPI.getWorkflows()` (Store 已有)

**3. 完善工作流画布 (40 min)**
- 文件: `fe/src/components/workflow/WorkflowCanvas.tsx`
- 核心实现:
```tsx
import { ReactFlow, Background, Controls, MiniMap, addEdge, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const nodeTypes = { start: StartNode, agent: AgentNode, condition: ConditionNode, code: CodeNode, end: EndNode };

// 从 URL params 获取 workflow_id → GET /api/workflow/get/{id} 加载
// 拖拽: onDrop → 添加节点
// 连线: onConnect → addEdge
// 保存: 收集 nodes + edges → PUT /api/workflow/update/{id}
// 执行: POST /api/workflow/execute/{id} → 消费 SSE
```
- 三栏布局: NodePanel(左) | ReactFlow(中) | PropertyPanel(右)
- 顶部工具栏: [← 返回] [名称] [保存] [执行]

**4. 完善 5 种自定义节点 (30 min)**
- 文件: `fe/src/components/workflow/nodes/StartNode.tsx` — 绿色，1 输出 Handle
- 文件: `fe/src/components/workflow/nodes/AgentNode.tsx` — 蓝色，显示 Agent 名称，1 输入 + 1 输出
- 文件: `fe/src/components/workflow/nodes/ConditionNode.tsx` — 黄色，1 输入 + 2 输出 (true/false)
- 文件: `fe/src/components/workflow/nodes/CodeNode.tsx` — 紫色，1 输入 + 1 输出
- 文件: `fe/src/components/workflow/nodes/EndNode.tsx` — 红色，1 输入
- 每个节点:
```tsx
import { Handle, Position } from '@xyflow/react';
const AgentNode = ({ data, selected }) => (
  <div className={`workflow-node agent-node ${selected ? 'selected' : ''}`}>
    <Handle type="target" position={Position.Left} />
    <div className="node-header">🤖 Agent</div>
    <div className="node-body">{data.agent_name || '未选择'}</div>
    <Handle type="source" position={Position.Right} />
  </div>
);
```

**5. 完善节点面板 + 属性面板 (15 min)**
- 文件: `fe/src/components/workflow/NodePanel.tsx` — 5 种节点拖拽列表
- 文件: `fe/src/components/workflow/PropertyPanel.tsx` — 选中节点的配置表单:
  - Agent 节点: 下拉选 Agent（`agentAPI.getAgents()`）
  - Condition: 表达式输入
  - Code: TextArea 代码编辑
  - End: 输出 key

**6. 工作流节点 CSS 样式 (10 min)**
- 文件: `fe/src/components/workflow/workflow.css`
- 节点颜色、选中态、Handle 样式

**交付物**: 完整的工作流可视化编辑器（拖拽、连线、配置、保存、执行）

---

### 8.6 前端工程师 B — 路由导航 + MCP 增强 + 模型管理

**职责**: 全局路由接入、MCP 页面增强、模型管理页面完善

#### 任务清单 (2h15m)

**1. 更新路由和导航 (20 min)**
- 文件: `fe/src/components/layout/Layout.tsx`
- 改动:
  - 导入 WorkflowList, WorkflowCanvas, ModelProvider
  - 新增路由:
```tsx
<Route path="/workflows" element={<WorkflowList />} />
<Route path="/workflows/:id" element={<WorkflowCanvas />} />
<Route path="/models" element={<ModelProvider />} />
```
  - 更新 menuItems:
```tsx
{ key: '3', icon: <ApartmentOutlined />, label: <Link to="/workflows">工作流</Link> },
{ key: '5', icon: <CloudServerOutlined />, label: <Link to="/models">模型管理</Link> },
```
  - 更新 selectedKey 路径检测

**2. 修复 API 路径不一致 (20 min)**
- 文件: `fe/src/services/api.ts`
- 修复 WORKFLOW_API:
```typescript
const WORKFLOW_API = {
  list: `${BASE_URL}/workflow/list`,
  create: `${BASE_URL}/workflow/create`,
  get: (id: string) => `${BASE_URL}/workflow/get/${id}`,
  update: (id: string) => `${BASE_URL}/workflow/update/${id}`,
  delete: (id: string) => `${BASE_URL}/workflow/delete/${id}`,
  execute: (id: string) => `${BASE_URL}/workflow/execute/${id}`,
  nodeTypes: `${BASE_URL}/workflow/node-types`,
  executions: (id: string) => `${BASE_URL}/workflow/executions/${id}`,
};

const MODEL_API = {
  list: `${BASE_URL}/model/providers`,
  create: `${BASE_URL}/model/provider`,
  get: (id: string) => `${BASE_URL}/model/provider/${id}`,
  update: (id: string) => `${BASE_URL}/model/provider/${id}`,
  delete: (id: string) => `${BASE_URL}/model/provider/${id}`,
  test: (id: string) => `${BASE_URL}/model/provider/${id}/test`,
  availableModels: `${BASE_URL}/model/available-models`,
};
```

**3. 增强 MCP 页面 (30 min)**
- 文件: `fe/src/components/mcp/MCP.tsx`
- 新增:
  - 表格列: 分组(Tag)、状态(Badge: running=绿/error=红/unknown=灰)、工具数(可点击)
  - 顶部分组筛选下拉
  - 每行 "健康检查" 按钮 → `mcpStore.healthCheck(id)`
  - "全部检查" 按钮 → `mcpStore.healthCheckAll()`
  - 点击工具数 → `mcpStore.getServerTools(server)` → Modal 列表
  - 创建/编辑 Modal: 新增 group(Select) + tags(Select mode=tags)

**4. 完善模型管理页面 (30 min)**
- 文件: `fe/src/components/model/ModelProvider.tsx`
- 内容:
  - Table: 名称、类型(Tag)、模型数、状态(Badge)、操作
  - Modal: type Select → 动态配置表单
  - "测试连接" 按钮 → `modelAPI.testConnection(id)`

**5. 更新 TypeScript 类型 (10 min)**
- 文件: `fe/src/types/index.ts`
- 确保 Workflow/ModelProvider/MCPServer 类型完整

**交付物**: 路由导航 + MCP 增强 + 模型管理页面 + API 路径修复

---

## 九、集成联调方案

### 9.1 联调顺序（第 2:30 - 2:50 阶段）

```
Step 1  后端 C 运行建表脚本 + Seed 数据 → 确认 DynamoDB 表创建成功
        ↓
Step 2  后端 A 启动 FastAPI → 验证 /docs 所有接口正常
        ↓
Step 3  前端 B 更新路由 → 验证导航跳转正常
        ↓
Step 4  前端 B 修复 API 路径 → 前端 A 的工作流列表可加载数据
        ↓
Step 5  前端 A + 后端 A 联调:
        工作流画布保存 → 后端存储 → 刷新页面重新加载
        ↓
Step 6  前端 B + 后端 A 联调:
        MCP 健康检查 UI → 后端接口 → 状态刷新
        模型管理 CRUD → 后端接口 → 列表刷新
```

### 9.2 冒烟测试用例

| # | 场景 | 操作 | 预期结果 |
|---|------|------|---------|
| 1 | 新建工作流 | 工作流列表 → 新建 → 输入名称 | 跳转到画布页面 |
| 2 | 拖拽节点 | 从左侧面板拖拽 Start、Agent、End 到画布 | 画布显示 3 个节点 |
| 3 | 连线 | 从 Start 输出 Handle 拖拽到 Agent 输入 Handle | 两节点间出现连线 |
| 4 | 保存工作流 | 点击保存按钮 | Toast "保存成功"，刷新页面后恢复 |
| 5 | 执行工作流 | 点击执行按钮 | SSE 流式返回节点状态（后端日志可见） |
| 6 | MCP 健康检查 | MCP 列表 → 某 Server → 健康检查 | 状态 Badge 从灰变绿/红 |
| 7 | MCP 查看工具 | 点击工具数 | Modal 显示工具名称和描述列表 |
| 8 | 创建 Provider | 模型管理 → 新建 → 选 bedrock | 列表出现新 Provider |
| 9 | 测试连接 | Provider 行 → 测试连接 | 返回 "Connected, N models" |
| 10 | Agent 选择模型 | Agent 编辑 → 模型选择 | 下拉包含 active Provider 的模型 |

### 9.3 联调 Debug 检查清单

| 问题 | 检查点 |
|------|--------|
| 前端 404 | 检查 `api.ts` 路径是否与后端 router prefix 一致 |
| CORS 错误 | 检查 `main.py` CORS 中间件 |
| DynamoDB 找不到表 | 运行 `create_tables.py`，检查 AWS_REGION 环境变量 |
| SSE 无响应 | 检查 `Accept: text/event-stream` Header |
| 工作流执行失败 | 检查 Agent 节点的 agent_id 是否存在于 AgentTable |

---

## 十、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| **ReactFlow 学习曲线** | 中 | 高 | 前端 A 可参考 ReactFlow 官方 examples；核心只需 nodes/edges/onConnect |
| **前后端 API 路径不一致** | 高 | 高 | 前端 B 第一优先级修复 api.ts；已在 §8.6 列出所有不一致项 |
| **工作流执行需要真实 Agent** | 中 | 中 | Seed 数据包含 1 个 Bedrock Agent；执行测试需 AWS 凭证 |
| **DynamoDB 建表权限** | 低 | 中 | 后端 C 提前准备建表脚本，或手动在 Console 创建 |
| **3 小时时间不够** | 中 | 中 | 优先保证: ① 路由导航 ② 工作流列表+画布 ③ API 路径修复；执行可视化可降级 |
| **MCP 健康检查阻塞** | 低 | 低 | 使用 asyncio + 超时控制（已实现） |

### 降级策略

如果时间不够：
1. **必须完成**: 路由导航更新 + 工作流列表页 + API 路径修复
2. **尽量完成**: 工作流画布（可先只支持新增节点和保存，不做执行可视化）
3. **可延后**: MCP 页面增强 + 模型管理页面（后端已完备，前端下次补）

---

## 十一、迭代路线图

| 迭代 | 时间 | 重点内容 | 关键交付 |
|------|------|---------|---------|
| **Sprint 1** | Day 1 (3h) | P0 MVP | 工作流画布 + 路由 + MCP 增强 + 模型管理 |
| **Sprint 2** | Week 1 | 工作流增强 | 执行可视化（节点高亮）+ 高级节点（Loop/HTTP） |
| **Sprint 3** | Week 2 | 知识库 MVP | PostgreSQL+pgvector + 文档上传 + 向量检索 |
| **Sprint 4** | Week 3 | MCP 智能路由 + 可观测性 | 语义工具发现 + Token 消耗仪表盘 |
| **Sprint 5** | Week 4 | 应用发布 | Agent/Workflow → API Endpoint + API Key |
| **Sprint 6** | Week 5-6 | Human-in-the-Loop + 版本管理 | 工作流暂停/恢复 + Draft/Published |
| **Sprint 7** | Week 7-8 | Multi-Agent + RAG 2.0 | Swarm 模式 + 混合检索 |
| **Sprint 8** | Week 9-10 | Marketplace + RBAC | 模板市场 + 角色权限 |

---

## 附录 A：项目目录结构（完整）

### 后端 (`be/app/`)

```
be/app/
├── __init__.py
├── main.py                  # FastAPI 入口 + 路由注册 + CORS
├── agent/                   # Agent 模块（现有）
│   ├── __init__.py
│   ├── agent.py             # AgentPO + AgentPOService + build_strands_agent
│   ├── event_serializer.py  # SSE 事件序列化
│   └── event_models.py      # 事件类型定义
├── mcp/                     # MCP 模块（现有 + 增强）
│   ├── __init__.py
│   └── mcp.py               # HttpMCPServer + MCPService（含分组/健康检查/工具发现）
├── workflow/                 # 🆕 工作流模块
│   ├── __init__.py
│   ├── models.py            # WorkflowPO + WorkflowExecution + WorkflowService + WorkflowExecutionService
│   ├── engine.py            # WorkflowEngine — DAG BFS 遍历 + SSE 事件
│   └── nodes.py             # 5 种节点执行器 + NODE_TYPE_DEFINITIONS
├── model/                   # 🆕 模型管理模块
│   ├── __init__.py
│   ├── models.py            # ModelProviderPO
│   └── service.py           # ModelProviderService（CRUD + 连通测试 + 模型聚合）
├── schedule/                # 调度模块（现有）
│   ├── __init__.py
│   ├── models.py
│   └── service.py
├── routers/                 # API 路由层
│   ├── __init__.py
│   ├── agent.py             # /agent/* 路由
│   ├── mcp.py               # /mcp/* 路由（含增强接口）
│   ├── chat_record.py       # /chat/* 路由
│   ├── schedule.py          # /schedule/* 路由
│   ├── workflow.py           # 🆕 /workflow/* 路由（8 个接口）
│   └── model.py             # 🆕 /model/* 路由（7 个接口）
├── utils/
│   ├── __init__.py
│   └── aws_config.py        # AWS Region 配置
├── scripts/                 # 🆕 运维脚本
│   ├── create_tables.py     # DynamoDB 建表
│   └── seed_data.py         # 初始数据
└── tests/                   # 🆕 测试
    ├── test_workflow_e2e.py
    ├── test_nodes.py
    ├── test_engine.py
    └── test_integration.py
```

### 前端 (`fe/src/`)

```
fe/src/
├── main.tsx                 # 入口
├── App.tsx
├── components/
│   ├── layout/
│   │   └── Layout.tsx       # 全局布局 + 路由（需更新）
│   ├── chat/                # 对话（现有）
│   │   ├── Chat.tsx
│   │   ├── ChatList.tsx
│   │   └── ChatInput.tsx
│   ├── agent/               # Agent 管理（现有）
│   │   └── Agent.tsx
│   ├── mcp/                 # MCP Hub（需增强）
│   │   └── MCP.tsx
│   ├── schedule/            # 调度（现有）
│   │   └── Schedule.tsx
│   ├── workflow/            # 🆕 工作流模块
│   │   ├── WorkflowList.tsx     # 列表页
│   │   ├── WorkflowCanvas.tsx   # 画布主容器
│   │   ├── NodePanel.tsx        # 左侧节点面板
│   │   ├── PropertyPanel.tsx    # 右侧属性面板
│   │   ├── types.ts             # 工作流本地类型
│   │   ├── workflow.css         # 🆕 样式
│   │   ├── nodes/               # 自定义节点
│   │   │   ├── StartNode.tsx
│   │   │   ├── AgentNode.tsx
│   │   │   ├── ConditionNode.tsx
│   │   │   ├── CodeNode.tsx
│   │   │   ├── EndNode.tsx
│   │   │   └── index.ts
│   │   └── index.ts
│   └── model/               # 🆕 模型管理
│       ├── ModelProvider.tsx
│       └── index.ts
├── store/
│   ├── index.ts
│   ├── agentStore.ts        # 现有
│   ├── mcpStore.ts          # 现有（含健康检查/工具列表 action）
│   ├── scheduleStore.ts     # 现有
│   ├── workflowStore.ts     # 🆕
│   └── modelStore.ts        # 🆕
├── services/
│   └── api.ts               # API 端点（需修复路径）
├── types/
│   └── index.ts             # TypeScript 类型（需确保完整）
├── hooks/
│   └── useAgent.ts
├── utils/
│   └── agentEventFormatter.ts
├── constants/
│   └── index.ts
└── styles/
    └── index.ts
```

---

## 附录 B：工作流节点类型定义（完整）

### P0 节点（5 种）

| 类型 | 标签 | 描述 | config 字段 | 输入 | 输出 |
|------|------|------|------------|------|------|
| `start` | 开始节点 | 工作流入口，透传 input_data | — | — | trigger_data |
| `agent` | Agent 节点 | 调用 Strands Agent 处理消息 | `agent_id`(必填), `user_message_template`(可选) | user_message | agent_response |
| `condition` | 条件节点 | 评估 Python 表达式，走 true/false 分支 | `expression`(必填) | data | true_branch / false_branch |
| `code` | 代码节点 | 执行 Python 代码片段 | `code`(必填) | data | result |
| `end` | 结束节点 | 收集最终输出 | `output_keys`(可选) | data | — |

### P1 扩展节点（4 种）

| 类型 | 标签 | 描述 |
|------|------|------|
| `http` | HTTP 节点 | 发送 HTTP 请求，支持 GET/POST/PUT/DELETE |
| `loop` | 循环节点 | 遍历列表，对每个元素执行子工作流 |
| `parallel` | 并行节点 | 同时执行多个分支 |
| `llm` | LLM 节点 | 直接调用模型（不通过 Agent），用于简单文本处理 |

---

## 附录 C：关键设计决策记录 (ADR)

### ADR-001: 保持 FastAPI 单体架构（不微服务化）

- **决策**: 2.0 MVP 保持 FastAPI 单体，不做微服务拆分
- **理由**: 5 人团队 + 3 小时 Sprint，微服务增加部署复杂度，单体够用
- **何时重新评估**: 当请求量 > 1000 QPS 或团队 > 15 人时

### ADR-002: DynamoDB 存储工作流定义（非 PostgreSQL）

- **决策**: definition 字段存为 JSON 字符串在 DynamoDB 中
- **理由**: 一致性（全部用 DynamoDB），工作流定义不需要关系查询
- **权衡**: definition 大小受 DynamoDB 400KB item 限制，足够绝大多数工作流

### ADR-003: 工作流 definition 存为 JSON 字符串（非 DynamoDB Map）

- **决策**: definition 字段类型为 String（JSON 序列化），非 DynamoDB 原生 Map
- **理由**: ReactFlow 前端产生的 nodes/edges 结构嵌套较深，DynamoDB Map 有 400KB 限制但深度嵌套难调试。JSON 字符串可直接 loads/dumps，前后端统一
- **代码体现**: `WorkflowPO.definition: str = "{}"`

### ADR-004: 向量数据库选择 pgvector（非 OpenSearch）

- **决策**: P1 知识库使用 PostgreSQL + pgvector，不用 Amazon OpenSearch
- **理由**:
  - pgvector 更轻量，与 PostgreSQL 复用一个实例
  - 万级文档检索性能足够
  - OpenSearch 成本较高，运维复杂
- **DESIGN.md 中提到 OpenSearch**: 降级为 3.0 备选方案

### ADR-005: Agent 模型构建集成 ModelProviderTable

- **决策**: `AgentPOService._build_model()` 自动查询 ModelProviderTable 获取 Provider 配置
- **理由**: 统一模型配置管理，避免每个 Agent 都要手动填写 API Key
- **降级**: 如果 ModelProviderTable 不存在或查询失败，使用 Agent 自身的 extras 配置
- **代码位置**: `be/app/agent/agent.py` 第 370-400 行

### ADR-006: 前后端 API 路径统一风格

- **决策**: 后端使用 `/resource/action/id` 风格（如 `/workflow/get/{id}`），前端 api.ts 必须对齐
- **理由**: 现有 Agent 接口已是这种风格，保持一致
- **注意**: 前端 api.ts 原有路径不一致（如 `/workflow/{id}`），Sprint 中必须修复

---

## 附录 D：环境变量参考

```bash
# AWS 配置
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# 应用配置
APP_ENV=production          # production 时 API 前缀为 /api
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# DynamoDB 表名（硬编码在代码中，此处列出供参考）
# AgentTable, HttpMCPTable, AgentScheduleTable, ChatRecordTable, ChatResponseTable
# WorkflowTable, WorkflowExecutionTable, ModelProviderTable
```

---

> **文档完成。工程师拿到此文档后，从 §八 开始，按照自己的角色（后端 A/B/C 或前端 A/B）直接开始编码。如有疑问，回到对应章节查阅详细设计。**
>
> **核心原则回顾**：
> 1. 在现有代码基础上增量开发
> 2. 后端模块已基本完整，Sprint 重点是前端完善 + 联调
> 3. 前端 api.ts 路径修复是联调成功的关键前提
> 4. MVP 务实 — 能跑通 > 功能丰富
