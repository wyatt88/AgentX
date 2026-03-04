# AgentX 2.0 — 产品设计文档

> 版本: v1.0 | 作者: AI 产品经理 | 日期: 2026-03-04

---

## 一、产品愿景

**一句话定义**: AgentX 2.0 是一个以 Agent 为核心、工作流为骨架、MCP 为工具层的统一 AI 自动化平台。

**核心差异化**: 不同于 Dify（AI 应用构建）或 n8n（通用工作流自动化），AgentX 2.0 的独特定位是 **"Strands-Native Agent Orchestration"** — 以 AWS Strands SDK 为运行时引擎，让 Agent 既能独立对话，又能作为工作流节点被编排，同时共享统一的 MCP 工具池和知识库。

**产品名称建议**: 保持 **AgentX** 品牌，版本升级为 2.0。副标题: *"AI Agent Orchestration Platform"*。

### 与竞品的关键区别

| 维度 | AgentX 2.0 | Dify | n8n |
|------|-----------|------|-----|
| Agent 运行时 | Strands SDK（AWS 原生） | 自研 Agent 引擎 | LangChain 集成 |
| 工作流 | Agent-first DAG | AI Workflow | 通用 500+ 集成 |
| MCP 管理 | 内置 Hub（智能路由） | 插件式 MCP Client | 无原生 MCP |
| 部署目标 | EKS / AWS 原生 | Docker Compose | Docker / Cloud |
| 核心用户 | AI 工程师 + 平台团队 | AI 应用开发者 | 运维 / 自动化团队 |

---

## 二、产品架构

### 2.1 分层架构（自上而下）

```
┌─────────────────────────────────────────────────────────┐
│                    展示层 (React + Ant Design)            │
│  Agent 管理 | 工作流画布 | MCP Hub | 知识库 | 对话 | 监控  │
├─────────────────────────────────────────────────────────┤
│                    API 网关层 (FastAPI)                   │
│  RESTful API + WebSocket + SSE 流式                      │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Agent   │ Workflow │   MCP    │Knowledge │ Observability│
│  Engine  │  Engine  │   Hub    │  (RAG)   │   System     │
│ (Strands)│ (DAG执行)│(工具管理) │(向量检索) │  (追踪统计)  │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    模型管理层 (Model Gateway)              │
│  Bedrock | OpenAI | Ollama | LiteLLM | 自定义            │
├─────────────────────────────────────────────────────────┤
│                    存储层                                 │
│  DynamoDB(元数据) | PostgreSQL+pgvector(向量) | S3(文件)  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 各层职责

| 层 | 职责 | 技术选型 |
|----|------|---------|
| **展示层** | 用户交互、工作流画布、Agent 配置 | React + TypeScript + Ant Design + ReactFlow |
| **API 层** | 路由、鉴权、请求转发 | FastAPI + WebSocket |
| **Agent Engine** | Agent 生命周期管理、对话、Agent-as-Tool | Strands SDK (现有) |
| **Workflow Engine** | DAG 解析、节点执行、条件分支、并行 | 自研轻量引擎 (Python) |
| **MCP Hub** | MCP Server 注册/发现/分组/健康检查 | 扩展现有 mcp/ 模块 |
| **Knowledge** | 文档上传、分块、向量化、混合检索 | PostgreSQL + pgvector + Bedrock Embedding |
| **Observability** | Token 统计、延迟追踪、调用链 | 内存统计 + DynamoDB 持久化 |
| **Model Gateway** | 多模型切换、Provider 管理 | 扩展现有 model provider |
| **存储层** | 结构化数据 + 向量 + 文件 | DynamoDB + PostgreSQL + S3 |

---

## 三、功能模块清单

### P0 — 必须实现（3小时 MVP）

| 模块 | 功能 | 说明 |
|------|------|------|
| **Agent 管理** | CRUD + 对话（保留现有） | 现有功能，微调 UI |
| **工作流引擎** | 可视化 DAG 编辑器 | ReactFlow 拖拽画布，支持 5 种基础节点 |
| **工作流节点** | Start / Agent / Condition / Code / End | 最小可用节点集 |
| **工作流执行** | 顺序执行 + 条件分支 | 后端 DAG 遍历引擎 |
| **MCP Hub** | MCP Server 集中管理 + 分组 | 扩展现有 MCP CRUD，增加分组和状态 |
| **MCP 健康检查** | 连通性检测 + 状态展示 | 调用 MCP Server 的 list_tools 验证 |
| **模型管理** | 多 Provider 配置页面 | 从 Agent 表单中抽离为独立管理 |

### P1 — 重要功能（后续迭代 1-2 周）

| 模块 | 功能 | 说明 |
|------|------|------|
| **知识库** | 文档上传 + 分块 + 向量检索 | PostgreSQL + pgvector |
| **工作流高级节点** | Loop / Parallel / HTTP / LLM | 扩展节点类型 |
| **Human-in-the-Loop** | 工作流暂停等待人工确认 | 暂停 + 恢复机制 |
| **MCP 智能路由** | 语义搜索匹配最佳工具 | pgvector + Embedding |
| **应用发布** | Agent/Workflow 一键发布为 API | 生成独立 API endpoint |
| **可观测性** | Token 消耗 + 延迟 + 调用链 | 仪表盘页面 |
| **工作流版本** | Draft / Published 状态 | 版本管理 |

### P2 — 未来规划（1-3 月）

| 模块 | 功能 |
|------|------|
| **Marketplace** | 工作流模板 + Agent 模板市场 |
| **Multi-Agent** | Swarm / Graph 多 Agent 协作 |
| **RAG 2.0** | 混合检索策略、自定义 Pipeline |
| **WebApp 发布** | 一键生成独立 Chatbot 页面 |
| **RBAC** | 角色权限管理 |
| **API Key 轮转** | 模型 API Key 负载均衡 |
| **导入导出** | 工作流 YAML/JSON 导入导出 |

---

## 四、页面/路由规划

### 4.1 整体导航结构

```
/ (根路由 → 重定向 /chat)
├── /chat                    # Agent 对话（现有，保留）
├── /agents                  # Agent 管理（现有 /agent，重命名）
│   └── /agents/:id/edit     # Agent 编辑详情
├── /workflows               # 🆕 工作流列表
│   ├── /workflows/new       # 🆕 新建工作流（画布）
│   └── /workflows/:id       # 🆕 工作流编辑（画布）
├── /mcp                     # MCP Hub（现有，增强）
│   └── /mcp/:id             # MCP Server 详情
├── /models                  # 🆕 模型管理
├── /knowledge               # 🆕 知识库（P1）
│   └── /knowledge/:id       # 知识库详情
├── /apps                    # 🆕 应用发布（P1）
└── /monitor                 # 🆕 监控面板（P1）
```

### 4.2 P0 阶段页面清单（6个页面）

| 页面 | 路由 | 说明 | 改动类型 |
|------|------|------|---------|
| Agent 对话 | /chat | 现有对话页面 | 微调 |
| Agent 管理 | /agents | 现有列表，重命名路由 | 微调 |
| **工作流列表** | /workflows | 工作流卡片列表 + 新建按钮 | 🆕 新建 |
| **工作流画布** | /workflows/:id | ReactFlow 拖拽画布 + 节点面板 + 属性面板 | 🆕 新建 |
| MCP Hub | /mcp | 增加分组管理、健康状态徽标 | 增强 |
| **模型管理** | /models | 模型 Provider 列表 + 配置 | 🆕 新建 |

### 4.3 侧边栏导航更新

```
📋 Agent X 2.0
├── 💬 对话           → /chat
├── 🤖 Agents        → /agents
├── 🔀 工作流         → /workflows     (🆕)
├── 🔧 MCP Hub       → /mcp
├── 🧠 模型管理       → /models        (🆕)
├── 📚 知识库         → /knowledge     (P1)
├── 📊 监控          → /monitor        (P1)
└── 🚀 应用          → /apps           (P1)
```

---

## 五、数据模型设计

### 5.1 现有实体（保留，微调）

#### Agent 表 (DynamoDB: AgentTable)
```
{
  id: string (PK)          # UUID
  name: string             # 英文标识符
  display_name: string     # 显示名称
  description: string      # 描述
  agent_type: number       # 1=plain, 2=orchestrator
  model_provider: number   # 1=bedrock, 2=openai, ...
  model_id: string         # 模型标识
  sys_prompt: string       # 系统提示词
  tools: List[AgentTool]   # 工具列表
  envs: string             # 环境变量
  extras: dict             # 扩展字段(base_url, api_key 等)
  created_at: string       # 🆕 创建时间
  updated_at: string       # 🆕 更新时间
}
```

#### MCP Server 表 (DynamoDB: HttpMCPTable) — 增强
```
{
  id: string (PK)          # UUID
  name: string             # Server 名称
  desc: string             # 描述
  host: string             # Streamable HTTP URL
  group: string            # 🆕 分组名称 (默认 "default")
  status: string           # 🆕 "running" | "stopped" | "error"
  health_check_at: string  # 🆕 上次健康检查时间
  tools_count: number      # 🆕 工具数量(缓存)
  tags: List[string]       # 🆕 标签
  created_at: string       # 🆕 创建时间
  updated_at: string       # 🆕 更新时间
}
```

### 5.2 新增实体

#### Workflow 表 (DynamoDB: WorkflowTable)
```
{
  id: string (PK)          # UUID
  name: string             # 工作流名称
  description: string      # 描述
  status: string           # "draft" | "published" | "archived"
  definition: string       # JSON 序列化的 DAG 定义 (见下方)
  trigger_type: string     # "manual" | "schedule" | "webhook"
  trigger_config: dict     # 触发配置(cron 表达式/webhook path)
  created_at: string
  updated_at: string
  published_at: string     # 最近发布时间
}
```

#### Workflow Definition (JSON 结构，存在 definition 字段中)
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "start",
      "position": {"x": 100, "y": 200},
      "data": {}
    },
    {
      "id": "node_2",
      "type": "agent",
      "position": {"x": 300, "y": 200},
      "data": {
        "agent_id": "xxx",
        "input_mapping": {"user_message": "{{node_1.output}}"}
      }
    },
    {
      "id": "node_3",
      "type": "condition",
      "position": {"x": 500, "y": 200},
      "data": {
        "expression": "{{node_2.output}} contains 'error'"
      }
    },
    {
      "id": "node_4",
      "type": "code",
      "position": {"x": 700, "y": 100},
      "data": {
        "language": "python",
        "code": "return {'result': inputs['data'].upper()}"
      }
    },
    {
      "id": "node_5",
      "type": "end",
      "position": {"x": 900, "y": 200},
      "data": {"output_key": "final_result"}
    }
  ],
  "edges": [
    {"id": "e1", "source": "node_1", "target": "node_2"},
    {"id": "e2", "source": "node_2", "target": "node_3"},
    {"id": "e3", "source": "node_3", "target": "node_4", "label": "true"},
    {"id": "e4", "source": "node_3", "target": "node_5", "label": "false"}
  ]
}
```

#### Workflow Execution 表 (DynamoDB: WorkflowExecutionTable)
```
{
  id: string (PK)              # 执行 ID
  workflow_id: string (GSI)    # 工作流 ID
  status: string               # "running" | "completed" | "failed" | "paused"
  trigger_type: string         # 触发方式
  input_data: string           # 输入数据 JSON
  output_data: string          # 输出数据 JSON
  node_states: string          # 各节点执行状态 JSON
  error_message: string        # 错误信息
  started_at: string
  completed_at: string
  total_tokens: number         # Token 消耗总计
  total_duration_ms: number    # 总耗时
}
```

#### Model Provider 表 (DynamoDB: ModelProviderTable)
```
{
  id: string (PK)          # UUID
  name: string             # 显示名称 ("AWS Bedrock", "OpenAI", ...)
  type: string             # "bedrock" | "openai" | "ollama" | "litellm" | "custom"
  config: dict             # 配置信息
    # bedrock: {region: "us-west-2"}
    # openai: {base_url: "...", api_key: "..."}
    # ollama: {base_url: "http://localhost:11434"}
  models: List[string]     # 可用模型列表
  is_default: boolean      # 是否默认 Provider
  status: string           # "active" | "inactive"
  created_at: string
  updated_at: string
}
```

---

## 六、API 设计

### 6.1 现有 API（保留）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/agent/list | 获取 Agent 列表 |
| GET | /api/agent/get/{id} | 获取单个 Agent |
| POST | /api/agent/createOrUpdate | 创建/更新 Agent |
| DELETE | /api/agent/delete/{id} | 删除 Agent |
| POST | /api/agent/stream_chat | 流式对话 (SSE) |
| POST | /api/agent/async_chat | 异步对话 |
| GET | /api/agent/tool_list | 可用工具列表 |
| GET | /api/mcp/list | MCP Server 列表 |
| POST | /api/mcp/createOrUpdate | 创建/更新 MCP Server |
| DELETE | /api/mcp/delete/{id} | 删除 MCP Server |
| GET | /api/schedule/list | 调度任务列表 |
| POST | /api/schedule/create | 创建调度 |
| PUT | /api/schedule/update/{id} | 更新调度 |
| DELETE | /api/schedule/delete/{id} | 删除调度 |
| GET | /api/chat/list_record | 对话记录列表 |
| GET | /api/chat/list_chat_responses | 对话响应列表 |
| DELETE | /api/chat/del_chat | 删除对话 |

### 6.2 新增 API — 工作流

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| GET | /api/workflow/list | 工作流列表 | — |
| GET | /api/workflow/get/{id} | 获取工作流详情 | — |
| POST | /api/workflow/create | 创建工作流 | `{name, description, definition}` |
| PUT | /api/workflow/update/{id} | 更新工作流 | `{name, description, definition}` |
| DELETE | /api/workflow/delete/{id} | 删除工作流 | — |
| POST | /api/workflow/publish/{id} | 发布工作流 | — |
| POST | /api/workflow/execute/{id} | 执行工作流 | `{input_data}` |
| GET | /api/workflow/execution/{exec_id} | 获取执行状态 | — |
| GET | /api/workflow/executions/{wf_id} | 工作流执行历史 | — |
| GET | /api/workflow/node-types | 可用节点类型列表 | — |

### 6.3 新增 API — MCP Hub 增强

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/mcp/groups | 获取 MCP 分组列表 |
| PUT | /api/mcp/update/{id} | 更新 MCP Server（增加 group, tags） |
| POST | /api/mcp/health-check/{id} | 触发单个 Server 健康检查 |
| POST | /api/mcp/health-check-all | 触发全部 Server 健康检查 |
| GET | /api/mcp/tools/{server_id} | 获取某 Server 的工具列表 |

### 6.4 新增 API — 模型管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/model/providers | 模型 Provider 列表 |
| GET | /api/model/provider/{id} | 获取 Provider 详情 |
| POST | /api/model/provider | 创建 Provider |
| PUT | /api/model/provider/{id} | 更新 Provider |
| DELETE | /api/model/provider/{id} | 删除 Provider |
| POST | /api/model/provider/{id}/test | 测试 Provider 连通性 |
| GET | /api/model/available-models | 所有可用模型（聚合） |

### 6.5 关键 API 详细设计

#### POST /api/workflow/execute/{id}

```json
// Request
{
  "input_data": {
    "user_message": "分析一下今天的销售数据",
    "context": {}
  }
}

// Response (SSE stream)
event: node_start
data: {"node_id": "node_1", "node_type": "start", "timestamp": "..."}

event: node_complete
data: {"node_id": "node_1", "output": {...}, "duration_ms": 12}

event: node_start
data: {"node_id": "node_2", "node_type": "agent", "timestamp": "..."}

event: agent_stream
data: {"node_id": "node_2", "delta": {"text": "根据分析..."}}

event: node_complete
data: {"node_id": "node_2", "output": {...}, "duration_ms": 3500, "tokens": 1200}

event: workflow_complete
data: {"execution_id": "xxx", "status": "completed", "total_duration_ms": 5000, "total_tokens": 1500}
```

#### POST /api/mcp/health-check/{id}

```json
// Response
{
  "server_id": "xxx",
  "status": "running",
  "tools": [
    {"name": "query_database", "description": "Execute SQL query"},
    {"name": "list_tables", "description": "List all tables"}
  ],
  "tools_count": 2,
  "latency_ms": 150,
  "checked_at": "2026-03-04T19:00:00Z"
}
```

---

## 七、技术方案

### 7.1 关键技术选型

| 技术点 | 选型 | 理由 |
|--------|------|------|
| **工作流画布** | ReactFlow | React 生态最成熟的 DAG 编辑库，MIT 协议，社区活跃，n8n/Dify 也用类似方案 |
| **工作流执行引擎** | 自研轻量 Python DAG Runner | Strands Agent 已处理 AI 推理，引擎只需做 DAG 拓扑排序 + 节点调度，无需引入重量级框架 |
| **向量数据库** | PostgreSQL + pgvector | 复用 PostgreSQL，不引入新组件；pgvector 够用于万级文档 |
| **Agent 运行时** | Strands SDK（保持） | 现有核心，不换 |
| **MCP 协议** | Streamable HTTP（保持） | 现有方案，扩展分组和健康检查 |
| **状态管理** | Zustand（保持） | 现有方案，轻量够用 |
| **数据库** | DynamoDB（保持）+ PostgreSQL（新增） | DynamoDB 存元数据（低延迟），PostgreSQL 存向量和工作流执行日志 |
| **文件存储** | S3 | 知识库文档原文件存储（P1） |

### 7.2 工作流引擎设计

#### 执行流程
```
1. 解析 workflow.definition JSON → 构建 DAG 图
2. 拓扑排序确定执行顺序
3. 从 Start 节点开始，依次执行每个节点
4. 遇到 Condition 节点 → 计算表达式 → 选择分支
5. Agent 节点 → 调用 AgentPOService.stream_chat()
6. Code 节点 → exec() 执行 Python 代码（沙箱）
7. 每个节点执行完毕 → 输出存入 context → SSE 推送状态
8. 到达 End 节点 → 汇总结果 → 标记执行完成
```

#### 节点类型定义（P0 阶段 5 种）
```python
NODE_TYPES = {
    "start": {
        "name": "开始",
        "inputs": [],
        "outputs": ["trigger_data"],
        "config": {}
    },
    "agent": {
        "name": "Agent",
        "inputs": ["user_message"],
        "outputs": ["agent_response"],
        "config": {"agent_id": "string", "input_mapping": "dict"}
    },
    "condition": {
        "name": "条件分支",
        "inputs": ["data"],
        "outputs": ["true_branch", "false_branch"],
        "config": {"expression": "string"}
    },
    "code": {
        "name": "代码",
        "inputs": ["data"],
        "outputs": ["result"],
        "config": {"language": "python", "code": "string"}
    },
    "end": {
        "name": "结束",
        "inputs": ["data"],
        "outputs": [],
        "config": {"output_key": "string"}
    }
}
```

### 7.3 MCP 健康检查设计

```python
async def health_check(server: HttpMCPServer) -> dict:
    """
    1. 建立 MCPClient 连接到 server.host
    2. 调用 list_tools() 获取工具列表
    3. 记录延迟、工具数量、状态
    4. 更新 DynamoDB 中的 status 和 health_check_at
    5. 返回检查结果
    """
```

### 7.4 项目结构变更

#### 后端新增目录
```
be/app/
├── agent/           # 现有 - 不变
├── routers/
│   ├── agent.py     # 现有 - 不变
│   ├── mcp.py       # 现有 - 增强 (分组/健康检查接口)
│   ├── schedule.py  # 现有 - 不变
│   ├── chat_record.py # 现有 - 不变
│   ├── workflow.py  # 🆕 工作流路由
│   └── model.py     # 🆕 模型管理路由
├── mcp/
│   ├── mcp.py       # 现有 - 增强 (分组/健康检查/工具发现)
│   └── __init__.py
├── workflow/         # 🆕 工作流模块
│   ├── __init__.py
│   ├── models.py    # 工作流数据模型
│   ├── engine.py    # DAG 执行引擎
│   └── nodes.py     # 节点类型定义和执行逻辑
├── model/            # 🆕 模型管理模块
│   ├── __init__.py
│   ├── models.py    # 模型 Provider 数据模型
│   └── service.py   # 模型管理服务
├── schedule/        # 现有 - 不变
├── utils/           # 现有 - 不变
└── main.py          # 现有 - 增加新路由注册
```

#### 前端新增目录
```
fe/src/
├── components/
│   ├── agent/       # 现有 - 微调
│   ├── chat/        # 现有 - 不变
│   ├── mcp/         # 现有 - 增强
│   ├── schedule/    # 现有 - 不变
│   ├── layout/      # 现有 - 更新导航
│   ├── sidebar/     # 现有 - 不变
│   ├── workflow/    # 🆕 工作流模块
│   │   ├── WorkflowList.tsx      # 工作流列表页
│   │   ├── WorkflowCanvas.tsx    # 画布主容器
│   │   ├── nodes/                # 自定义节点组件
│   │   │   ├── StartNode.tsx
│   │   │   ├── AgentNode.tsx
│   │   │   ├── ConditionNode.tsx
│   │   │   ├── CodeNode.tsx
│   │   │   └── EndNode.tsx
│   │   ├── NodePanel.tsx         # 左侧节点选择面板
│   │   ├── PropertyPanel.tsx     # 右侧属性配置面板
│   │   └── index.ts
│   └── model/       # 🆕 模型管理
│       ├── ModelProvider.tsx      # 模型 Provider 管理页
│       └── index.ts
├── store/
│   ├── agentStore.ts    # 现有
│   ├── mcpStore.ts      # 现有 - 增强
│   ├── workflowStore.ts # 🆕 工作流状态
│   └── modelStore.ts    # 🆕 模型状态
├── services/
│   └── api.ts           # 现有 - 增加新 API
└── types/
    └── index.ts         # 现有 - 增加新类型
```

---

## 八、开发任务拆解（3小时 Sprint）

### 总体时间分配

| 阶段 | 时间 | 内容 |
|------|------|------|
| 0:00 - 0:15 | 15 min | 全员阅读文档，确认理解，环境准备 |
| 0:15 - 2:30 | 135 min | 并行开发 |
| 2:30 - 2:50 | 20 min | 集成联调 |
| 2:50 - 3:00 | 10 min | 冒烟测试 + 录屏 Demo |

---

### 后端工程师 A — 工作流引擎（核心）

**职责**: 工作流数据模型 + DAG 执行引擎 + API 路由

#### 任务清单

**1. 创建工作流数据模型 (20 min)**
- 文件: `be/app/workflow/__init__.py`, `be/app/workflow/models.py`
- 内容:
  - `WorkflowPO(BaseModel)` — id, name, description, status, definition(JSON str), trigger_type, trigger_config, created_at, updated_at, published_at
  - `WorkflowExecution(BaseModel)` — id, workflow_id, status, input_data, output_data, node_states, error_message, started_at, completed_at, total_tokens, total_duration_ms
  - `WorkflowService` — CRUD 操作，使用 DynamoDB `WorkflowTable` 和 `WorkflowExecutionTable`
  - 参考现有 `be/app/agent/agent.py` 中 `AgentPOService` 的 DynamoDB 操作模式

**2. 创建节点类型定义 (20 min)**
- 文件: `be/app/workflow/nodes.py`
- 内容:
  - `NodeType` 枚举: start, agent, condition, code, end
  - `NodeExecutor` 基类 + 每种节点的执行器
  - `StartNodeExecutor.execute(context)` → 透传 input_data
  - `AgentNodeExecutor.execute(context)` → 调用 `AgentPOService.stream_chat()`，收集完整响应
  - `ConditionNodeExecutor.execute(context)` → eval 表达式，返回 true/false 分支
  - `CodeNodeExecutor.execute(context)` → exec() 执行 Python 代码，传入 inputs dict
  - `EndNodeExecutor.execute(context)` → 收集最终输出

**3. 实现 DAG 执行引擎 (40 min)**
- 文件: `be/app/workflow/engine.py`
- 内容:
  ```python
  class WorkflowEngine:
      def __init__(self, workflow: WorkflowPO):
          self.workflow = workflow
          self.definition = json.loads(workflow.definition)
          self.nodes = {n['id']: n for n in self.definition['nodes']}
          self.edges = self.definition['edges']
          self.context = {}  # node_id → output

      async def execute(self, input_data: dict) -> AsyncGenerator:
          """执行工作流，yield SSE 事件"""
          execution_id = uuid.uuid4().hex
          start_node = self._find_start_node()
          self.context['input'] = input_data

          # BFS/DFS 遍历 DAG
          queue = [start_node['id']]
          visited = set()

          while queue:
              node_id = queue.pop(0)
              if node_id in visited:
                  continue
              visited.add(node_id)

              node = self.nodes[node_id]
              yield {"event": "node_start", "node_id": node_id, "node_type": node['type']}

              # 执行节点
              executor = self._get_executor(node['type'])
              result = await executor.execute(node, self.context)
              self.context[node_id] = result

              yield {"event": "node_complete", "node_id": node_id, "output": result}

              # 查找后继节点
              next_nodes = self._get_next_nodes(node_id, result)
              queue.extend(next_nodes)

          yield {"event": "workflow_complete", "execution_id": execution_id}
  ```

**4. 创建工作流 API 路由 (30 min)**
- 文件: `be/app/routers/workflow.py`
- 内容:
  - `GET /workflow/list` → `WorkflowService.list_workflows()`
  - `GET /workflow/get/{id}` → `WorkflowService.get_workflow(id)`
  - `POST /workflow/create` → 验证 definition JSON + `WorkflowService.add_workflow()`
  - `PUT /workflow/update/{id}` → 更新工作流
  - `DELETE /workflow/delete/{id}` → 删除工作流
  - `POST /workflow/execute/{id}` → `WorkflowEngine.execute()` 返回 SSE StreamingResponse
  - `GET /workflow/node-types` → 返回可用节点类型定义
  - `GET /workflow/executions/{wf_id}` → 执行历史列表

**5. 注册路由 (5 min)**
- 文件: `be/app/main.py`
- 修改: 导入 workflow 和 model 路由，`app.include_router(workflow.router, prefix=url_prefix)`

**交付物**: 工作流 CRUD + 可执行的 DAG 引擎 + SSE 流式执行反馈

---

### 后端工程师 B — MCP Hub 增强 + 模型管理

**职责**: MCP 分组/健康检查 + 模型 Provider 管理

#### 任务清单

**1. 增强 MCP 数据模型 (15 min)**
- 文件: `be/app/mcp/mcp.py`
- 修改:
  - `HttpMCPServer` 模型新增字段: group(str), status(str), health_check_at(str), tools_count(int), tags(List[str])
  - `MCPService` 新增方法:
    - `list_groups()` → scan + 按 group 聚合
    - `list_by_group(group)` → scan + FilterExpression
    - `update_server(id, data)` → put_item 更新

**2. 实现 MCP 健康检查 (30 min)**
- 文件: `be/app/mcp/mcp.py` (在 MCPService 类中新增)
- 内容:
  ```python
  async def health_check(self, server_id: str) -> dict:
      server = self.get_mcp_server(server_id)
      try:
          mcp_client = MCPClient(lambda: streamablehttp_client(server.host))
          mcp_client = mcp_client.start()
          tools = mcp_client.list_tools_sync()
          # 更新 DynamoDB: status=running, tools_count, health_check_at
          return {"status": "running", "tools": tools, "tools_count": len(tools)}
      except Exception as e:
          # 更新 DynamoDB: status=error
          return {"status": "error", "error": str(e)}
      finally:
          mcp_client.stop()

  async def get_server_tools(self, server_id: str) -> list:
      """获取某 MCP Server 的工具列表"""
      server = self.get_mcp_server(server_id)
      mcp_client = MCPClient(lambda: streamablehttp_client(server.host))
      mcp_client = mcp_client.start()
      tools = mcp_client.list_tools_sync()
      mcp_client.stop()
      return [{"name": t.name, "description": t.description} for t in tools]
  ```

**3. 增强 MCP API 路由 (20 min)**
- 文件: `be/app/routers/mcp.py`
- 新增接口:
  - `GET /mcp/groups` → MCPService.list_groups()
  - `PUT /mcp/update/{id}` → MCPService.update_server()
  - `POST /mcp/health-check/{id}` → MCPService.health_check()
  - `POST /mcp/health-check-all` → 遍历所有 server 执行 health_check
  - `GET /mcp/tools/{server_id}` → MCPService.get_server_tools()

**4. 创建模型管理模块 (30 min)**
- 文件: `be/app/model/__init__.py`, `be/app/model/models.py`, `be/app/model/service.py`
- 内容:
  - `ModelProviderPO(BaseModel)` — id, name, type, config(dict), models(List[str]), is_default(bool), status(str), created_at, updated_at
  - `ModelProviderService` — DynamoDB `ModelProviderTable` 的 CRUD
  - `test_connection(provider)` — 根据 type 调用模型 API 测试连通性
    - bedrock: `boto3.client('bedrock-runtime').invoke_model()` 简单测试
    - openai: `requests.get(base_url + '/models')` 测试
    - ollama: `requests.get(base_url + '/api/tags')` 测试

**5. 创建模型 API 路由 (20 min)**
- 文件: `be/app/routers/model.py`
- 内容:
  - `GET /model/providers` → 列表
  - `GET /model/provider/{id}` → 详情
  - `POST /model/provider` → 创建
  - `PUT /model/provider/{id}` → 更新
  - `DELETE /model/provider/{id}` → 删除
  - `POST /model/provider/{id}/test` → 测试连通性
  - `GET /model/available-models` → 聚合所有 active provider 的模型列表

**6. 注册路由 (5 min)**
- 文件: `be/app/main.py`
- 修改: 导入 model 路由，`app.include_router(model.router, prefix=url_prefix)`

**交付物**: MCP 分组管理 + 健康检查 + 模型 Provider 完整管理

---

### 后端工程师 C — 工作流执行持久化 + Agent/MCP 胶水层

**职责**: 执行记录存储、Agent 模块微调、DynamoDB 建表脚本、集成测试

#### 任务清单

**1. DynamoDB 表创建脚本 (15 min)**
- 文件: `be/scripts/create_tables.py`（新建）
- 内容: 创建 `WorkflowTable`, `WorkflowExecutionTable`, `ModelProviderTable` 的 boto3 脚本
  - WorkflowTable: PK=id
  - WorkflowExecutionTable: PK=id, GSI: workflow_id-index (workflow_id, started_at)
  - ModelProviderTable: PK=id
- 或者提供 CDK 更新（如果用 CDK 管理）

**2. 工作流执行持久化 (25 min)**
- 文件: `be/app/workflow/models.py` (补充 WorkflowExecutionService)
- 内容:
  - `save_execution(execution)` → DynamoDB put_item
  - `get_execution(exec_id)` → get_item
  - `list_executions(workflow_id)` → query by GSI
  - `update_execution_status(exec_id, status, output)` → update_item
- 与后端工程师 A 的 engine.py 集成: engine 执行完毕后调用 save_execution()

**3. Agent 模块微调 (20 min)**
- 文件: `be/app/agent/agent.py`
- 修改:
  - `AgentPO` 增加 `created_at`, `updated_at` 字段
  - `AgentPOService.add_agent()` 自动填充时间戳
  - `AgentPOService.build_strands_agent()` 增加对 ModelProvider 表的查询: 如果 agent.model_provider 对应的 provider 在 ModelProviderTable 中有记录，优先使用其 config
  - 抽取模型构建逻辑为独立方法 `_build_model(provider, model_id, extras)` 减少代码重复

**4. Agent 工具列表增强 (15 min)**
- 文件: `be/app/agent/agent.py`
- 修改 `get_all_available_tools()`:
  - MCP 工具增加 group 信息
  - MCP 工具增加 status 信息（只返回 running 状态的 server 工具）

**5. API 集成测试脚本 (30 min)**
- 文件: `be/tests/test_workflow.py`, `be/tests/test_mcp_enhanced.py`, `be/tests/test_model.py`
- 内容:
  - 工作流: 创建 → 获取 → 更新 → 执行 → 查看执行历史 → 删除
  - MCP: 创建带 group 的 server → 分组查询 → 健康检查 → 工具列表
  - 模型: 创建 provider → 测试连通性 → 可用模型列表

**6. main.py 统一注册 + CORS 配置 (10 min)**
- 文件: `be/app/main.py`
- 修改:
  - 导入所有新路由
  - 添加 CORS 中间件（如果没有的话）
  - 添加全局异常处理

**交付物**: 建表脚本 + 执行持久化 + Agent 微调 + 集成测试

---

### 前端工程师 A — 工作流画布（核心新功能）

**职责**: ReactFlow 工作流编辑器 + 节点组件 + 工作流列表

#### 任务清单

**1. 安装 ReactFlow 依赖 (5 min)**
- 文件: `fe/package.json`
- 命令: `npm install @xyflow/react`

**2. 创建工作流列表页 (25 min)**
- 文件: `fe/src/components/workflow/WorkflowList.tsx`
- 内容:
  - Ant Design Card 列表布局（参考现有 Agent 列表风格）
  - 每个 Card 显示: 工作流名称、描述、状态(draft/published)徽标、节点数量、最后更新时间
  - 操作按钮: 编辑(跳转画布)、执行、删除
  - 右上角 "新建工作流" 按钮 → Modal 输入名称和描述 → 创建后跳转画布
  - 调用 `GET /api/workflow/list`
- 文件: `fe/src/components/workflow/index.ts` — 导出

**3. 创建工作流画布主容器 (40 min)**
- 文件: `fe/src/components/workflow/WorkflowCanvas.tsx`
- 内容:
  - 三栏布局: 左侧节点面板(200px) | 中间 ReactFlow 画布 | 右侧属性面板(300px)
  - ReactFlow 初始化:
    ```tsx
    import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
    import '@xyflow/react/dist/style.css';

    const nodeTypes = {
      start: StartNode,
      agent: AgentNode,
      condition: ConditionNode,
      code: CodeNode,
      end: EndNode,
    };

    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
      fitView
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
    ```
  - 顶部工具栏: 工作流名称(可编辑) | 保存按钮 | 发布按钮 | 执行按钮 | 返回列表
  - 拖拽节点到画布: 从左侧 NodePanel 拖拽到画布触发 `onDrop` → 添加节点
  - 节点连线: ReactFlow 内置 `onConnect` 回调
  - 保存: 收集 nodes + edges → `PUT /api/workflow/update/{id}`
  - 页面从 URL params 获取 workflow_id → `GET /api/workflow/get/{id}` 加载

**4. 创建 5 种自定义节点组件 (30 min)**
- 文件: `fe/src/components/workflow/nodes/StartNode.tsx`
  - 绿色圆角卡片，图标 ▶，1个输出 Handle
- 文件: `fe/src/components/workflow/nodes/AgentNode.tsx`
  - 蓝色卡片，显示 Agent 名称 + 模型信息，1个输入 + 1个输出 Handle
- 文件: `fe/src/components/workflow/nodes/ConditionNode.tsx`
  - 黄色菱形卡片，显示条件表达式，1个输入 + 2个输出 Handle (true/false)
- 文件: `fe/src/components/workflow/nodes/CodeNode.tsx`
  - 紫色卡片，显示代码片段预览，1个输入 + 1个输出 Handle
- 文件: `fe/src/components/workflow/nodes/EndNode.tsx`
  - 红色圆角卡片，图标 ⏹，1个输入 Handle

每个节点组件结构:
```tsx
import { Handle, Position } from '@xyflow/react';

const AgentNode = ({ data, selected }) => (
  <div className={`workflow-node agent-node ${selected ? 'selected' : ''}`}>
    <Handle type="target" position={Position.Left} />
    <div className="node-header">🤖 Agent</div>
    <div className="node-body">{data.agent_name || '未选择 Agent'}</div>
    <Handle type="source" position={Position.Right} />
  </div>
);
```

**5. 创建节点选择面板 (15 min)**
- 文件: `fe/src/components/workflow/NodePanel.tsx`
- 内容:
  - 5 种节点类型列表，每种显示图标+名称+描述
  - 支持拖拽（HTML5 Drag API: onDragStart 设置 nodeType）
  - 拖拽到画布时触发 WorkflowCanvas 的 onDrop

**6. 创建属性配置面板 (20 min)**
- 文件: `fe/src/components/workflow/PropertyPanel.tsx`
- 内容:
  - 选中节点时显示属性配置表单
  - Agent 节点: 下拉选择 Agent（从 /api/agent/list 获取）+ 输入映射配置
  - Condition 节点: 表达式输入框
  - Code 节点: 代码编辑器（用 Ant Design TextArea 或简单的 textarea，P1 再接 Monaco Editor）
  - End 节点: 输出 key 名称
  - 属性变更时更新 ReactFlow 节点 data

**交付物**: 完整的工作流可视化编辑器（拖拽创建节点、连线、配置属性、保存）

---

### 前端工程师 B — MCP Hub 增强 + 模型管理 + 路由/导航

**职责**: MCP 页面增强、模型管理页面、全局路由更新、工作流 Store

#### 任务清单

**1. 更新全局路由和导航 (15 min)**
- 文件: `fe/src/components/layout/Layout.tsx`
- 修改:
  - 导入 WorkflowList, WorkflowCanvas, ModelProvider 组件
  - 新增路由:
    ```tsx
    <Route path="/workflows" element={<WorkflowList />} />
    <Route path="/workflows/:id" element={<WorkflowCanvas />} />
    <Route path="/models" element={<ModelProvider />} />
    ```
  - 更新 menuItems 数组:
    ```tsx
    { key: '1', icon: <CommentOutlined />, label: <Link to="/chat">对话</Link> },
    { key: '2', icon: <RobotOutlined />, label: <Link to="/agents">Agents</Link> },
    { key: '3', icon: <ApartmentOutlined />, label: <Link to="/workflows">工作流</Link> },
    { key: '4', icon: <ApiOutlined />, label: <Link to="/mcp">MCP Hub</Link> },
    { key: '5', icon: <CloudServerOutlined />, label: <Link to="/models">模型管理</Link> },
    { key: '6', icon: <ScheduleOutlined />, label: <Link to="/schedule">调度</Link> },
    ```

**2. 创建工作流 Store + API (20 min)**
- 文件: `fe/src/store/workflowStore.ts`
- 内容:
  ```typescript
  interface WorkflowState {
    workflows: Workflow[];
    currentWorkflow: Workflow | null;
    loading: boolean;
    fetchWorkflows: () => Promise<void>;
    createWorkflow: (data: CreateWorkflowReq) => Promise<Workflow>;
    updateWorkflow: (id: string, data: UpdateWorkflowReq) => Promise<void>;
    deleteWorkflow: (id: string) => Promise<void>;
    executeWorkflow: (id: string, inputData: any) => Promise<Response>;  // SSE
  }
  ```
- 文件: `fe/src/services/api.ts`
- 新增 WORKFLOW_API 和 MODEL_API 端点定义 + workflowAPI 和 modelAPI 函数

**3. 创建模型 Store (10 min)**
- 文件: `fe/src/store/modelStore.ts`
- 内容: ModelProviderState — providers列表, CRUD 操作, 测试连通性

**4. 增强 MCP 页面 (30 min)**
- 文件: `fe/src/components/mcp/MCP.tsx`
- 修改:
  - 表格新增列: 分组(Tag)、状态(Badge: running=绿/stopped=灰/error=红)、工具数
  - 新增 "分组筛选" 下拉框（顶部）
  - 创建/编辑 Modal 增加字段: group(Select), tags(Select mode=tags)
  - 每行增加操作: "健康检查" 按钮 → 调用 POST /api/mcp/health-check/{id} → 刷新状态
  - 顶部增加 "全部检查" 按钮 → POST /api/mcp/health-check-all
  - 点击工具数 → Modal 显示该 Server 的工具列表（调用 GET /api/mcp/tools/{id}）
- 文件: `fe/src/store/mcpStore.ts`
- 新增: healthCheck, healthCheckAll, fetchGroups, getServerTools 方法

**5. 创建模型管理页面 (30 min)**
- 文件: `fe/src/components/model/ModelProvider.tsx`
- 内容:
  - Ant Design Table 列表: 名称、类型(Tag)、可用模型数、状态(Badge)、操作
  - 创建/编辑 Modal:
    - 类型选择(Select): bedrock/openai/ollama/litellm/custom
    - 根据类型动态显示配置项:
      - bedrock: Region 输入框
      - openai: Base URL + API Key 输入框（密码模式）
      - ollama: Base URL 输入框
    - 可用模型列表(Select mode=tags): 手动输入或从列表选择
    - 是否默认(Switch)
  - 操作: "测试连接" 按钮 → POST /api/model/provider/{id}/test → 显示成功/失败
  - 删除确认

**6. 更新 TypeScript 类型 (10 min)**
- 文件: `fe/src/types/index.ts`
- 新增:
  ```typescript
  // Workflow types
  export interface Workflow {
    id: string; name: string; description: string;
    status: 'draft' | 'published' | 'archived';
    definition: WorkflowDefinition;
    trigger_type: string; trigger_config: any;
    created_at: string; updated_at: string;
  }
  export interface WorkflowDefinition {
    nodes: WorkflowNode[]; edges: WorkflowEdge[];
  }
  export interface WorkflowNode {
    id: string; type: string;
    position: {x: number; y: number};
    data: Record<string, any>;
  }
  export interface WorkflowEdge {
    id: string; source: string; target: string; label?: string;
  }

  // Model Provider types
  export interface ModelProvider {
    id: string; name: string; type: string;
    config: Record<string, any>; models: string[];
    is_default: boolean; status: string;
  }
  ```

**交付物**: 路由导航更新 + MCP Hub 增强页面 + 模型管理页面 + 全部 Store 和 API

---

## 九、集成联调检查清单

### 联调顺序（第 2:30-2:50 阶段）

1. **后端 C** 运行建表脚本，确认 DynamoDB 表创建成功
2. **后端 A + C** 联调: 工作流创建 → 执行 → 执行记录持久化
3. **后端 B** 独立验证: MCP 健康检查 + 模型 Provider CRUD
4. **前端 B** 更新路由后，**前端 A** 的工作流页面可通过导航访问
5. **前端 A + 后端 A** 联调: 工作流画布保存 → 后端存储 → 重新加载
6. **前端 B + 后端 B** 联调: MCP 健康检查 UI → 后端接口 → 状态刷新

### 冒烟测试用例

| # | 场景 | 预期结果 |
|---|------|---------|
| 1 | 创建一个包含 Start → Agent → End 的工作流 | 画布显示三个节点和两条连线 |
| 2 | 保存工作流 → 刷新页面 | 节点和连线恢复 |
| 3 | 执行工作流 | 后端返回 SSE 事件流，前端可观察到执行状态 |
| 4 | MCP 健康检查 | 状态徽标从灰色变为绿色/红色 |
| 5 | 创建 OpenAI 模型 Provider | 列表中出现新 Provider，测试连通性返回结果 |
| 6 | Agent 创建时选择模型 | 下拉列表包含所有 active Provider 的模型 |

---

## 十、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| ReactFlow 学习成本 | 中 | 高 | 前端 A 可参考 ReactFlow 官方示例，核心只需 nodes/edges/onConnect |
| 工作流执行引擎复杂度 | 中 | 高 | P0 只做顺序+条件分支，不做并行和循环 |
| MCP 健康检查阻塞 | 低 | 中 | 使用 asyncio 异步执行，设置超时 |
| DynamoDB 建表权限 | 低 | 中 | 后端 C 提前准备好建表脚本，或手动在控制台创建 |
| 3小时时间不够 | 中 | 中 | 优先保证工作流画布 + 后端 CRUD，执行引擎可简化为同步版 |

---

## 十一、后续迭代路线图

| 迭代 | 时间 | 重点 |
|------|------|------|
| Sprint 2 (1周) | Week 1 | 工作流高级节点(Loop/Parallel/HTTP)、工作流执行可视化(节点高亮)、知识库 MVP |
| Sprint 3 (1周) | Week 2 | MCP 智能路由(pgvector)、应用发布(API endpoint)、可观测性仪表盘 |
| Sprint 4 (2周) | Week 3-4 | Human-in-the-Loop、工作流版本管理、RAG Pipeline、Multi-Agent |
| Sprint 5 (2周) | Week 5-6 | Marketplace、WebApp 发布、RBAC、导入导出 |

---

## 附录 A: 工作流节点颜色规范

| 节点类型 | 颜色 | 图标 | 形状 |
|---------|------|------|------|
| Start | #52c41a (绿) | ▶ PlayCircle | 圆角矩形 |
| Agent | #1890ff (蓝) | 🤖 Robot | 矩形 |
| Condition | #faad14 (黄) | ⚡ Branch | 菱形 |
| Code | #722ed1 (紫) | </> Code | 矩形 |
| End | #ff4d4f (红) | ⏹ Stop | 圆角矩形 |
| HTTP (P1) | #13c2c2 (青) | 🌐 Global | 矩形 |
| Loop (P1) | #eb2f96 (粉) | 🔄 Sync | 矩形 |

## 附录 B: DynamoDB 表清单

| 表名 | PK | GSI | 说明 |
|------|-----|-----|------|
| AgentTable | id | — | 现有，保留 |
| HttpMCPTable | id | — | 现有，扩展字段 |
| AgentScheduleTable | id | — | 现有，保留 |
| ChatRecordTable | id | — | 现有，保留 |
| ChatResponseTable | id + resp_no | — | 现有，保留 |
| **WorkflowTable** | id | — | 🆕 工作流定义 |
| **WorkflowExecutionTable** | id | workflow_id-index | 🆕 执行记录 |
| **ModelProviderTable** | id | — | 🆕 模型 Provider |

---

> **文档完成。工程师拿到此文档后可直接开始编码，无需再与产品经理确认。**
