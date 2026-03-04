# AgentX 功能文档

## 1. 产品概述

### 1.1 产品定位
AgentX 是基于 AWS Strands SDK 构建的企业级 AI Agent 管理平台，旨在为开发者和企业提供一站式的 AI Agent 开发、部署、管理和运营解决方案。平台支持多种 AI 模型提供商，提供丰富的工具生态，实现智能工作流的可视化编排与自动化执行。

### 1.2 核心价值
- **统一管理**：集中管理多个 AI Agent，支持不同类型的 Agent 协同工作
- **开放生态**：支持多种模型提供商和 MCP（Model Context Protocol）服务器集成
- **灵活扩展**：Agent-as-Tool 架构，支持复杂业务场景的模块化编排
- **企业就绪**：完整的部署方案、监控体系和权限管理

### 1.3 技术架构
- **前端**：React + TypeScript + Ant Design，响应式 Web 应用
- **后端**：基于 AWS Strands SDK，提供 RESTful API 和 SSE 流式接口
- **存储**：DynamoDB 分布式数据库，支持高并发读写
- **部署**：Docker 容器化 + AWS CDK 基础设施即代码
- **计算**：ECS Fargate + Lambda 无服务器架构

## 2. 功能模块详细说明

### 2.1 Agent 管理模块

#### 2.1.1 功能概述
Agent 管理是 AgentX 平台的核心模块，负责 AI Agent 的全生命周期管理，包括创建、配置、编辑、删除和监控。

#### 2.1.2 Agent 类型
**Plain Agent（普通 Agent）**
- 用途：执行单一特定任务的 AI Agent
- 特点：具备独立的推理能力和工具调用能力
- 应用场景：客服机器人、内容生成、数据分析等

**Orchestrator Agent（编排 Agent）**
- 用途：协调和管理多个 Plain Agent 的工作流
- 特点：可将其他 Agent 作为工具调用，实现复杂业务逻辑
- 应用场景：多步骤业务流程、跨领域任务编排

#### 2.1.3 配置项说明
| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 是 | Agent 唯一标识符，用于系统内部引用 |
| displayName | String | 是 | Agent 显示名称，用于用户界面展示 |
| description | String | 否 | Agent 功能描述和使用说明 |
| modelProvider | Enum | 是 | 模型提供商：Bedrock/OpenAI/Anthropic/LiteLLM/Ollama/Custom |
| modelId | String | 是 | 具体模型标识，如 claude-3-opus-20240229 |
| systemPrompt | Text | 是 | 系统提示词，定义 Agent 的角色和行为规范 |
| tools | Array | 否 | 可用工具列表，支持 Strands 内置工具、MCP 工具、Agent 工具 |
| environment | Object | 否 | 环境变量配置，支持 API Key、Base URL 等敏感信息 |
| extensions | Object | 否 | 扩展配置，支持自定义参数和高级设置 |

#### 2.1.4 操作流程
**创建 Agent**
1. 选择 Agent 类型（Plain/Orchestrator）
2. 配置基本信息（名称、描述）
3. 选择模型提供商和具体模型
4. 编写系统提示词
5. 配置工具权限
6. 设置环境变量（如需要）
7. 保存并激活

**编辑 Agent**
1. 从 Agent 列表选择目标 Agent
2. 修改配置项（支持热更新）
3. 测试配置变更
4. 保存更新

**删除 Agent**
1. 检查依赖关系（被其他 Agent 引用的不能删除）
2. 确认删除操作
3. 清理相关数据（对话记录、定时任务等）

### 2.2 模型支持模块

#### 2.2.1 支持的模型提供商
**AWS Bedrock（推荐）**
- 优势：原生集成、低延迟、企业级安全
- 支持模型：Claude 系列、Titan 系列
- 配置项：Region、重试策略、超时设置

**OpenAI**
- 支持自定义 base_url 和 api_key
- 兼容 OpenAI Compatible API 的服务
- 支持模型：GPT-4 系列、GPT-3.5 系列

**其他提供商**
- Anthropic：直接 API 调用
- LiteLLM：统一多提供商接口
- Ollama：本地部署模型
- Custom：自定义 HTTP 接口

#### 2.2.2 预设模型列表
| 模型名称 | 提供商 | 用途 | 特点 |
|----------|--------|------|------|
| Claude Opus 4 | Anthropic | 复杂推理任务 | 最高智能水平，适合复杂分析 |
| Claude Sonnet 4 | Anthropic | 平衡性能 | 速度与智能的最佳平衡 |
| Claude Sonnet 3.7 | Anthropic | 日常对话 | 快速响应，成本优化 |
| GPT-4o | OpenAI | 多模态处理 | 支持文本、图像、音频 |
| GPT-4 Turbo | OpenAI | 长文本处理 | 128K 上下文窗口 |
| kimi-k2 | 月之暗面 | 中文优化 | 中文理解和生成能力强 |

### 2.3 工具系统模块

#### 2.3.1 工具分类
AgentX 平台支持三种类型的工具，为 Agent 提供丰富的能力扩展：

**Strands 内置工具（14种）**
- RAG & Memory 类
  - `retrieve`：从知识库检索相关信息
  - `memory`：短期记忆存储和检索
  - `mem0_memory`：长期记忆管理

- 文件操作类
  - `editor`：代码编辑器功能
  - `file_read`：读取文件内容
  - `file_write`：写入文件内容

- 网络通信类
  - `http_request`：HTTP API 调用
  - `slack`：Slack 消息发送

- 多模态类
  - `image_reader`：图像识别和分析
  - `generate_image`：AI 图像生成
  - `nova_reels`：视频处理
  - `speak`：文本转语音

- 云服务类
  - `use_aws`：AWS 服务调用

- 实用工具类
  - `calculator`：数学计算
  - `current_time`：获取当前时间

- 专业工具类
  - `AgentCoreBrowser`：Web 浏览器自动化
  - `AgentCoreCodeInterpreter`：代码执行环境

**MCP Server 工具**
- 通过 Streamable HTTP 协议连接外部 MCP Server
- 动态加载工具列表，支持热插拔
- 支持第三方工具生态，如数据库连接、API 集成等

**Agent 工具**
- Plain Agent 可以被 Orchestrator Agent 当作工具调用
- 实现 Agent 之间的协作和复用
- 支持参数传递和结果返回

### 2.4 MCP Server 管理模块

#### 2.4.1 功能概述
MCP（Model Context Protocol）Server 管理模块负责外部工具服务的接入和管理，通过标准化的协议实现工具生态的扩展。

#### 2.4.2 数据模型
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | MCP Server 唯一标识符 |
| name | String | 是 | 服务名称 |
| description | String | 否 | 服务描述和功能说明 |
| host | String | 是 | Streamable HTTP URL |
| status | Enum | 自动 | 服务状态：Active/Inactive/Error |
| tools | Array | 自动 | 可用工具列表（动态获取） |
| createdAt | DateTime | 自动 | 创建时间 |
| updatedAt | DateTime | 自动 | 最后更新时间 |

#### 2.4.3 操作流程
**添加 MCP Server**
1. 填写服务基本信息（名称、描述、URL）
2. 系统自动连接测试
3. 获取可用工具列表
4. 保存服务配置

**工具同步**
- 定期检查 MCP Server 的工具更新
- 自动同步新增或删除的工具
- 通知相关 Agent 工具变更

#### 2.4.4 数据流
```
Agent 创建/编辑 → 选择 MCP Server → 获取工具列表 → 配置工具权限 → 运行时调用
```

### 2.5 对话系统模块

#### 2.5.1 功能概述
对话系统是用户与 Agent 交互的核心模块，支持实时流式对话和异步任务处理，提供完整的对话生命周期管理。

#### 2.5.2 对话模式
**流式对话（Stream Chat）**
- 接口：`POST /agent/stream_chat`
- 特点：Server-Sent Events (SSE) 实时流式响应
- 适用场景：实时对话、即时反馈需求
- 优势：低延迟、实时交互体验

**异步对话（Async Chat）**
- 接口：`POST /agent/async_chat`
- 特点：后台 BackgroundTask 异步处理
- 适用场景：长时间任务、批量处理、定时任务触发
- 优势：不阻塞用户界面、支持复杂计算

#### 2.5.3 数据持久化
**对话记录表（ChatRecordTable）**
- 存储对话的元数据信息
- 字段：对话ID、用户ID、Agent ID、创建时间、状态等

**对话响应表（ChatResponseTable）**
- 存储对话的详细内容
- 字段：响应ID、对话ID、消息类型、内容、时间戳等

#### 2.5.4 前端组件
- 基于 @ant-design/x 的 Chat 组件
- 支持实时渲染 Agent 事件流
- 消息类型：文本、图片、文件、工具调用结果
- 交互功能：重新生成、复制、导出对话

### 2.6 定时任务模块

#### 2.6.1 功能概述
定时任务模块基于 AWS EventBridge Scheduler + Lambda 架构，实现 Agent 的自动化执行和周期性任务调度。

#### 2.6.2 技术架构
```
Cron 表达式 → EventBridge Scheduler → Lambda 函数 → /agent/async_chat → Agent 执行
```

#### 2.6.3 数据模型（AgentScheduleTable）
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| scheduleId | String | 是 | 任务唯一标识符 |
| agentId | String | 是 | 关联的 Agent ID |
| name | String | 是 | 任务名称 |
| description | String | 否 | 任务描述 |
| cronExpression | String | 是 | Cron 表达式（5段格式） |
| inputMessage | String | 是 | 传递给 Agent 的消息 |
| isActive | Boolean | 是 | 任务是否激活 |
| lastExecuted | DateTime | 自动 | 最后执行时间 |
| nextExecution | DateTime | 自动 | 下次执行时间 |
| executionCount | Number | 自动 | 累计执行次数 |

#### 2.6.4 Cron 表达式格式
AgentX 使用5段 Cron 表达式，自动转换为 EventBridge 兼容格式：
```
* * * * * 
│ │ │ │ │
│ │ │ │ └─── 星期几 (0-6, 0=Sunday)
│ │ │ └───── 月份 (1-12)
│ │ └─────── 日期 (1-31)
│ └───────── 小时 (0-23)
└─────────── 分钟 (0-59)
```

示例：
- `0 9 * * 1-5`：工作日上午9点执行
- `*/15 * * * *`：每15分钟执行一次
- `0 0 1 * *`：每月1号午夜执行

### 2.7 前端应用模块

#### 2.7.1 技术栈
- **框架**：React 18 + TypeScript
- **构建工具**：Vite
- **UI 框架**：Ant Design 5.x
- **对话组件**：@ant-design/x
- **状态管理**：Zustand
- **路由**：React Router v6
- **HTTP 客户端**：Axios
- **样式方案**：CSS Modules + Less

#### 2.7.2 状态管理
**agentStore**
- Agent 列表管理
- Agent CRUD 操作状态
- 选中 Agent 信息

**mcpStore**
- MCP Server 列表
- 工具同步状态
- 连接状态监控

**scheduleStore**
- 定时任务列表
- 任务执行状态
- Cron 表达式验证

#### 2.7.3 页面布局
- **Sidebar 导航**：左侧固定导航栏，包含主要功能模块入口
- **主内容区**：右侧动态内容区域，根据路由切换页面
- **响应式设计**：支持桌面端和移动端适配

### 2.8 部署模块

#### 2.8.1 容器化架构
- **后端服务**：基于 Python FastAPI 的 Docker 镜像
- **前端服务**：基于 Nginx 的静态文件服务
- **MCP Servers**：4个独立的 MCP Server 容器
- **镜像管理**：AWS ECR 私有镜像仓库

#### 2.8.2 AWS 基础设施
- **计算服务**：ECS Fargate 无服务器容器
- **负载均衡**：Application Load Balancer (ALB)
- **数据存储**：DynamoDB 多表设计
- **消息队列**：EventBridge + Lambda
- **网络安全**：VPC + Security Groups
- **监控日志**：CloudWatch Logs

#### 2.8.3 部署流程
1. **构建镜像**：`build-and-push.sh` 脚本一键构建并推送到 ECR
2. **基础设施部署**：AWS CDK 部署 CloudFormation 模板
3. **服务更新**：ECS 滚动更新，零停机部署
4. **健康检查**：ALB 健康检查确保服务可用性

## 3. 用户角色与权限

### 3.1 当前权限模型
**单用户模式**
- 当前版本采用单用户设计
- 所有功能对用户完全开放
- 无角色区分和权限限制

### 3.2 规划的权限模型（2.0版本）

#### 3.2.1 用户角色定义
**超级管理员（Super Admin）**
- 系统全局配置权限
- 用户和角色管理
- 系统监控和维护

**管理员（Admin）**
- Agent 创建、编辑、删除
- MCP Server 管理
- 定时任务管理
- 用户管理（除超级管理员）

**开发者（Developer）**
- Agent 创建和编辑
- 对话测试和调试
- MCP Server 配置
- 查看监控数据

**使用者（User）**
- 与 Agent 对话
- 查看对话历史
- 基础配置修改

#### 3.2.2 权限矩阵
| 功能模块 | Super Admin | Admin | Developer | User |
|----------|-------------|--------|-----------|------|
| Agent 管理 | ✓ | ✓ | ✓ | ✗ |
| Agent 对话 | ✓ | ✓ | ✓ | ✓ |
| MCP Server | ✓ | ✓ | ✓ | ✗ |
| 定时任务 | ✓ | ✓ | ✓ | ✗ |
| 用户管理 | ✓ | ✓ | ✗ | ✗ |
| 系统配置 | ✓ | ✗ | ✗ | ✗ |
| 监控数据 | ✓ | ✓ | ✓ | ✗ |

## 4. 页面/路由规划

### 4.1 当前页面结构
```
/dashboard           # 总览仪表板
├── /agents          # Agent 管理
│   ├── /list        # Agent 列表
│   ├── /create      # 创建 Agent
│   ├── /edit/:id    # 编辑 Agent
│   └── /chat/:id    # Agent 对话
├── /mcp             # MCP Server 管理
│   ├── /list        # MCP Server 列表
│   └── /create      # 添加 MCP Server
└── /schedules       # 定时任务管理
    ├── /list        # 任务列表
    └── /create      # 创建任务
```

### 4.2 2.0 版本页面规划
```
/dashboard           # 总览仪表板
├── /agents          # Agent 管理
├── /workflows       # 工作流编辑器（新增）
├── /knowledge       # 知识库管理（新增）
├── /models          # 模型网关（新增）
├── /apps            # 应用发布（新增）
├── /monitoring      # 可观测性（新增）
├── /mcp             # MCP Server 管理
├── /schedules       # 定时任务管理
├── /users           # 用户管理（新增）
└── /settings        # 系统设置
```

## 5. API 接口清单

### 5.1 Agent 管理接口

#### 5.1.1 获取 Agent 列表
```http
GET /api/v1/agents
```

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": "agent_123",
      "name": "customer_service",
      "displayName": "客服助手",
      "description": "处理客户咨询和问题解答",
      "type": "plain",
      "modelProvider": "bedrock",
      "modelId": "claude-3-sonnet-20240229",
      "status": "active",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-02T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 1
  }
}
```

#### 5.1.2 创建 Agent
```http
POST /api/v1/agents
Content-Type: application/json

{
  "name": "data_analyst",
  "displayName": "数据分析师",
  "description": "数据分析和报告生成",
  "type": "plain",
  "modelProvider": "openai",
  "modelId": "gpt-4-turbo",
  "systemPrompt": "你是一名专业的数据分析师...",
  "tools": ["calculator", "file_read", "generate_image"],
  "environment": {
    "OPENAI_API_KEY": "sk-xxx",
    "OPENAI_BASE_URL": "https://api.openai.com/v1"
  }
}
```

#### 5.1.3 更新 Agent
```http
PUT /api/v1/agents/{agent_id}
```

#### 5.1.4 删除 Agent
```http
DELETE /api/v1/agents/{agent_id}
```

#### 5.1.5 获取 Agent 详情
```http
GET /api/v1/agents/{agent_id}
```

### 5.2 对话接口

#### 5.2.1 流式对话
```http
POST /api/v1/agents/{agent_id}/stream_chat
Content-Type: application/json

{
  "message": "帮我分析这份销售数据",
  "sessionId": "session_123",
  "attachments": ["file_id_1", "file_id_2"]
}
```

**SSE 响应格式：**
```
data: {"type": "start", "sessionId": "session_123"}
data: {"type": "text", "content": "我来帮您分析"}
data: {"type": "tool_call", "tool": "file_read", "args": {"file_id": "file_id_1"}}
data: {"type": "tool_result", "tool": "file_read", "result": "..."}
data: {"type": "text", "content": "分析结果如下..."}
data: {"type": "end"}
```

#### 5.2.2 异步对话
```http
POST /api/v1/agents/{agent_id}/async_chat
```

### 5.3 MCP Server 接口

#### 5.3.1 获取 MCP Server 列表
```http
GET /api/v1/mcp/servers
```

#### 5.3.2 添加 MCP Server
```http
POST /api/v1/mcp/servers

{
  "name": "database_connector",
  "description": "数据库连接工具",
  "host": "http://mcp-server:8000"
}
```

#### 5.3.3 获取 MCP Server 工具列表
```http
GET /api/v1/mcp/servers/{server_id}/tools
```

### 5.4 定时任务接口

#### 5.4.1 创建定时任务
```http
POST /api/v1/schedules

{
  "name": "daily_report",
  "description": "每日销售报告生成",
  "agentId": "agent_123",
  "cronExpression": "0 9 * * 1-5",
  "inputMessage": "生成昨日销售报告",
  "isActive": true
}
```

#### 5.4.2 获取任务执行历史
```http
GET /api/v1/schedules/{schedule_id}/executions
```

## 6. 2.0 新增功能详细规格

### 6.1 可视化工作流编辑器

#### 6.1.1 功能概述
基于拖拽的可视化工作流编辑器，允许用户通过图形界面设计复杂的 AI Agent 协作流程。

#### 6.1.2 核心特性
- **节点类型**：Agent 节点、条件判断节点、并行执行节点、数据转换节点
- **连接器**：支持有向图连接，定义数据流和控制流
- **参数传递**：节点间支持动态参数绑定和数据映射
- **版本控制**：工作流版本管理和回滚功能
- **模板库**：预置常用工作流模板

#### 6.1.3 技术实现
- 前端：React Flow 或 Antv X6 图编辑器
- 后端：工作流引擎，支持 DAG 执行
- 存储：工作流定义存储在 DynamoDB

### 6.2 MCP 智能路由 + 分组管理

#### 6.2.1 智能路由
- **意图识别**：基于 NLP 分析用户请求，智能选择合适的 MCP Server
- **负载均衡**：多个相同功能的 MCP Server 自动负载分配
- **故障转移**：主 Server 不可用时自动切换到备用 Server

#### 6.2.2 分组管理
- **逻辑分组**：按功能域对 MCP Server 进行分类管理
- **权限控制**：不同用户组对不同 Server 组的访问权限
- **监控告警**：分组级别的健康监控和告警通知

### 6.3 知识库 / RAG Pipeline

#### 6.3.1 功能架构
```
文档上传 → 向量化处理 → 存储到向量数据库 → 检索接口 → Agent 调用
```

#### 6.3.2 支持的文档类型
- 文本文件：PDF、Word、TXT、Markdown
- 网页内容：URL 爬取和解析
- 结构化数据：CSV、JSON、Excel
- 代码文件：支持多种编程语言

#### 6.3.3 检索策略
- **向量检索**：基于语义相似度的向量搜索
- **关键词检索**：传统 BM25 算法
- **混合检索**：向量 + 关键词的加权融合
- **重排序**：基于相关性的结果重排序

### 6.4 模型网关（负载均衡/Key轮转）

#### 6.4.1 负载均衡
- **轮询策略**：请求均匀分发到多个模型实例
- **权重分配**：基于模型性能和成本的智能分配
- **健康检查**：定期检测模型服务可用性

#### 6.4.2 API Key 管理
- **密钥池管理**：支持多个 API Key 的集中管理
- **自动轮转**：防止单个 Key 频率限制
- **成本控制**：基于 Key 的使用量统计和预算控制

### 6.5 应用发布（API/Chatbot/Webapp）

#### 6.5.1 API 发布
- **RESTful API**：将 Agent 封装为标准 REST 接口
- **API 文档**：自动生成 OpenAPI/Swagger 文档
- **认证授权**：API Key 或 OAuth2 认证机制

#### 6.5.2 Chatbot 发布
- **多平台集成**：支持微信、钉钉、Slack 等平台
- **对话管理**：会话保持和上下文管理
- **个性化配置**：头像、名称、欢迎语等定制

#### 6.5.3 Web 应用
- **一键部署**：基于模板快速生成 Web 应用
- **自定义界面**：支持主题、布局的个性化定制
- **嵌入集成**：iframe 或 JavaScript SDK 集成

### 6.6 可观测性（调用链/Token统计/延迟）

#### 6.6.1 调用链追踪
- **分布式追踪**：记录请求在系统中的完整路径
- **性能分析**：识别性能瓶颈和优化点
- **错误定位**：快速定位和诊断系统问题

#### 6.6.2 Token 统计
- **使用量统计**：按 Agent、用户、时间维度的 Token 消耗
- **成本分析**：基于不同模型价格的成本计算
- **预算告警**：使用量超限时的自动告警

#### 6.6.3 性能监控
- **响应延迟**：请求处理时间分布统计
- **吞吐量**：系统处理请求的 QPS/TPS 指标
- **可用性**：服务正常运行时间和故障率

## 7. 非功能性需求

### 7.1 性能要求

#### 7.1.1 响应时间
- **API 响应**：95% 请求在 200ms 内完成
- **流式对话**：首字节响应时间 < 500ms
- **页面加载**：首屏渲染时间 < 1s

#### 7.1.2 并发能力
- **同时用户**：支持 1000+ 并发用户
- **Agent 实例**：单个 Agent 支持 100+ 并发会话
- **吞吐量**：系统整体 QPS > 5000

#### 7.1.3 扩展性
- **水平扩展**：支持多实例部署和自动扩缩容
- **存储扩展**：DynamoDB 按需扩容，支持 PB 级数据
- **计算扩展**：基于 ECS Fargate 的弹性计算

### 7.2 安全要求

#### 7.2.1 认证授权
- **多因素认证**：支持 TOTP、SMS 等二次验证
- **角色权限**：基于 RBAC 的细粒度权限控制
- **API 安全**：JWT Token 认证和 API 密钥管理

#### 7.2.2 数据保护
- **传输加密**：全站 HTTPS，API 通信 TLS 1.3
- **存储加密**：DynamoDB 静态加密，敏感数据 AES-256
- **密钥管理**：AWS KMS 统一密钥管理

#### 7.2.3 隐私合规
- **数据匿名**：用户敏感信息脱敏处理
- **审计日志**：完整的操作审计和日志记录
- **合规认证**：支持 GDPR、SOC2 等合规要求

### 7.3 可用性要求

#### 7.3.1 高可用架构
- **多可用区**：跨 AZ 部署，99.9% 可用性保证
- **故障转移**：自动故障检测和服务切换
- **数据备份**：定期数据备份和灾难恢复

#### 7.3.2 监控告警
- **健康检查**：实时服务健康状态监控
- **告警机制**：多渠道告警通知（邮件、短信、钉钉）
- **自动恢复**：常见故障的自动修复机制

### 7.4 维护性要求

#### 7.4.1 部署运维
- **CI/CD 流水线**：自动化构建、测试和部署
- **灰度发布**：支持蓝绿部署和金丝雀发布
- **回滚机制**：快速回滚到稳定版本

#### 7.4.2 日志审计
- **结构化日志**：统一的日志格式和级别
- **日志聚合**：集中式日志收集和检索
- **长期存储**：日志归档和合规保存

## 8. 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| Agent | AI Agent | 基于大语言模型的智能代理，能够理解指令并执行任务 |
| Plain Agent | Plain Agent | 普通 Agent，执行特定单一任务的智能代理 |
| Orchestrator Agent | Orchestrator Agent | 编排 Agent，能够调用其他 Agent 协同完成复杂任务 |
| MCP | Model Context Protocol | 模型上下文协议，定义 AI 模型与外部工具交互的标准 |
| MCP Server | MCP Server | 基于 MCP 协议提供工具服务的服务器 |
| RAG | Retrieval Augmented Generation | 检索增强生成，结合外部知识库的文本生成技术 |
| SSE | Server-Sent Events | 服务器推送事件，用于实现服务器向客户端的实时数据推送 |
| Cron | Cron Expression | 定时任务表达式，用于定义任务的执行时间规律 |
| Token | Token | 大语言模型处理文本的基本单位，用于计量和计费 |
| 流式对话 | Stream Chat | 实时流式的对话模式，逐步返回响应内容 |
| 异步对话 | Async Chat | 异步处理的对话模式，适合长时间任务 |
| 工作流 | Workflow | 多个 Agent 协作的业务流程定义 |
| 向量化 | Vectorization | 将文本转换为数值向量的过程，用于语义检索 |
| 负载均衡 | Load Balancing | 将请求分发到多个服务实例，提高系统性能和可用性 |
| API 网关 | API Gateway | 统一的 API 入口，提供认证、限流、监控等功能 |
| 调用链 | Call Trace | 请求在分布式系统中的完整执行路径记录 |

---

## 结语

本文档详细描述了 AgentX 平台的功能架构和技术规格。随着产品的持续迭代和用户反馈，本文档将定期更新以保持与实际功能的一致性。

如有疑问或建议，请联系产品团队获得支持。