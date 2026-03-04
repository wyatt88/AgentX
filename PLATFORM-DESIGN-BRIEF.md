# AgentX 2.0 综合平台设计 Brief

## 背景

AgentX 是一个基于 Strands 框架的 Agent 管理平台，当前具备：
- Agent CRUD + 多模型支持 (Bedrock/OpenAI/LiteLLM/Ollama)
- MCP Server 集成（Streamable HTTP）
- Agent 编排 (Agent as Tool, Orchestrator 模式)
- 定时任务 (EventBridge + Lambda)
- WebSocket 流式对话
- React + Ant Design 前端
- FastAPI 后端 + DynamoDB 存储
- ECS + CDK 部署

## 目标

在 AgentX 现有基础上，融合 n8n、Dify、MCPHub 的设计理念，构建一个 **综合 AI Agent 平台**。

## 参考项目核心能力提取

### n8n — 工作流自动化
- **可视化工作流编辑器**（拖拽式 DAG，节点连线）
- **500+ 集成节点**（Trigger/Action/Cluster）
- **AI 工作流节点**（LangChain 集成，AI Agent/Memory/Tool/Chain 节点）
- **Queue 模式**（Redis + Worker 水平扩展）
- **Human-in-the-Loop**（子工作流暂停等人工审批）
- **版本控制**（工作流的 Publish/Draft 模式）
- **Subworkflow 复用**

### Dify — AI 应用平台
- **5 种应用类型**（Chatbot/Text Generator/Agent/Chatflow/Workflow）
- **完整 RAG Pipeline**（文档上传→分块→向量化→混合检索）
- **模型网关**（多模型切换 + 负载均衡 + API Key 轮转）
- **Marketplace 插件生态**
- **一键部署为 API/Webapp/Chatbot**
- **LLM 可观测性**（Token 消耗、延迟、调用链追踪）
- **MCP 双向集成**（作为 MCP Client + MCP Server）

### MCPHub — MCP 管理中枢
- **集中管理所有 MCP Server**
- **智能路由 ($smart)**（语义搜索匹配最佳工具）
- **分组管理**（按环境/团队/功能）
- **热更新配置**（增删 Server 无需重启）
- **OAuth 2.0 认证**
- **Progressive Disclosure**（省 Token 的工具发现模式）

### AgentX 现有 — Agent 管理
- **Agent = Model + Prompt + Tools + Env**
- **Strands 框架深度集成**
- **Agent as Tool**（Agent 编排）
- **MCP Server 动态加载**
- **定时调度**（EventBridge）
- **AWS 原生**（DynamoDB/ECS/Lambda/Bedrock）

## 设计要求

产品经理需要设计出一个综合平台，核心要求：

### 1. 统一的 Agent + Workflow 平台
- 保留 AgentX 的 Agent 管理核心
- 新增 **可视化工作流编辑器**（参考 n8n 的拖拽 DAG）
- Agent 可作为工作流节点使用
- 工作流支持条件分支、循环、并行、Human-in-the-Loop

### 2. MCP 管理中枢
- 融合 MCPHub 的集中管理理念
- 智能路由（语义搜索工具发现）
- 分组管理 + 热更新
- 作为平台的 "工具层" — Agent 和 Workflow 共享工具池

### 3. 知识库 / RAG
- 参考 Dify 的 RAG Pipeline
- 文档管理 + 向量化 + 混合检索
- 作为 Agent 的知识来源

### 4. 模型管理
- 多模型提供商（Bedrock/OpenAI/Anthropic/Ollama/自定义）
- 负载均衡 + API Key 轮转
- 模型性能监控

### 5. 应用发布
- 一键部署为 API/Chatbot/Webapp
- 应用共享 + 模板市场

### 6. 可观测性
- 调用链追踪
- Token 消耗统计
- 延迟监控
- 日志聚合

## 技术约束

- **前端**：React + TypeScript（在现有 AgentX fe/ 基础上扩展）
- **后端**：FastAPI + Python（在现有 AgentX be/ 基础上扩展）
- **数据库**：DynamoDB（现有）+ PostgreSQL + pgvector（新增，用于 RAG 和智能路由）
- **部署**：EKS（Kubernetes）优先
- **MCP Server**：保持现有 mcp/ 目录结构
- **AI 框架**：Strands SDK（保持，不换框架）

## 现有代码结构

```
AgentX/
├── be/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py        # 入口
│   │   ├── agent/         # Agent 核心逻辑
│   │   ├── routers/       # API 路由
│   │   ├── mcp/           # MCP 集成
│   │   ├── schedule/      # 定时任务
│   │   └── utils/         # 工具函数
│   ├── Dockerfile
│   └── pyproject.toml
├── fe/                    # React 前端
│   ├── src/
│   │   ├── components/    # UI 组件 (agent/chat/mcp/schedule/sidebar/layout)
│   │   ├── services/      # API 服务
│   │   ├── store/         # Zustand 状态管理
│   │   ├── types/         # TypeScript 类型
│   │   └── hooks/         # 自定义 Hooks
│   └── Dockerfile
├── mcp/                   # MCP Servers
│   ├── mysql/
│   ├── redshift/
│   ├── duckdb/
│   ├── opensearch/
│   └── aws-db/
└── cdk/                   # AWS CDK 部署
```

## 交付物

产品经理需输出：
1. **产品架构图**（文字描述）
2. **功能模块清单**（按优先级 P0/P1/P2）
3. **页面/路由规划**
4. **数据模型设计**
5. **API 设计**（核心接口）
6. **技术方案建议**
7. **开发任务拆解**（给 3 后端 + 2 前端工程师的任务分配）

## 参考资料位置

- n8n 知识：/data/knowledge/n8n-workflow-automation.md
- Dify 知识：/data/knowledge/dify-ai-platform.md
- MCPHub 知识：/data/knowledge/mcphub.md
- AgentX 代码：/data/AgentX/
- Strands SDK 知识：/data/knowledge/strands-agents-sdk.md
