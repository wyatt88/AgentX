# AgentX 平台设计文档

## 1. 项目概述与愿景

### 1.1 项目简介

AgentX 是一个基于 AWS Strands SDK 的企业级 AI Agent 管理平台，致力于降低 AI Agent 的构建、部署和运维门槛。平台遵循 **"Agent = LLM Model + System Prompt + Tools + Environment"** 的核心理念，为开发者和企业提供从 Agent 开发到生产部署的全生命周期管理能力。

### 1.2 核心价值

- **简化复杂性**：通过可视化界面和标准化工具链，让非技术用户也能构建实用的 AI Agent
- **标准化集成**：基于 MCP (Model Context Protocol) 协议统一工具生态，实现跨平台互操作
- **企业级可靠性**：提供完整的监控、调度、权限管理和可观测性能力
- **开放生态**：支持多种 LLM 模型和第三方工具，避免厂商锁定

### 1.3 平台愿景

**短期目标（1.0）**：构建稳定的 Agent CRUD 平台，支持基础的对话、工具调用和任务调度能力。

**中期目标（2.0）**：融合 n8n（工作流）+ Dify（RAG/模型网关）+ MCPHub（工具管理）的理念，打造企业级 AI 应用开发平台。

**长期目标（3.0+）**：成为 AI-Native 应用的操作系统，支持多 Agent 协作、自主学习和动态能力扩展。

## 2. 系统架构设计

### 2.1 当前架构（1.0）

```
┌─────────────────── 用户层 ───────────────────┐
│  React 前端 (Ant Design)  │  API 客户端      │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 应用层 ───────────────────┐
│           FastAPI 后端服务                   │
│  ┌─────────┬──────────┬──────────┬─────────┐ │
│  │ Agent   │   MCP    │  Chat    │Schedule │ │
│  │ 管理    │  服务    │  对话    │ 调度    │ │
│  └─────────┴──────────┴──────────┴─────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 数据层 ───────────────────┐
│                 DynamoDB                    │
│ ┌─────────┬──────────┬──────────┬─────────┐ │
│ │ Agent   │ Chat     │HttpMCP   │Schedule │ │
│ │ Table   │ Records  │ Table    │ Table   │ │
│ └─────────┴──────────┴──────────┴─────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 工具层 ───────────────────┐
│  ┌──────────────┬──────────────┬───────────┐ │
│  │ Strands 内置 │ MCP Servers  │ Agent     │ │
│  │ 工具         │ (HTTP 协议)  │ as Tool   │ │
│  └──────────────┴──────────────┴───────────┘ │
└─────────────────────────────────────────────┘
```

**架构特点**：
- 单体应用架构，易于部署和维护
- 基于 DynamoDB 的 NoSQL 数据存储
- RESTful API + WebSocket 的混合通信
- 容器化部署（ECS + ECR）

### 2.2 目标架构（2.0）

```
┌─────────────────── 用户层 ───────────────────┐
│ React 前端 │ 工作流编辑器 │ 应用发布页面    │
│ (管理控制台) │ (拖拽式 DAG) │ (API/Bot/Web)  │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 网关层 ───────────────────┐
│           统一 API 网关 + 负载均衡            │
│  ┌─────────────────────────────────────────┐ │
│  │  路由 │ 认证 │ 限流 │ 监控 │ 日志      │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 服务层 ───────────────────┐
│ ┌─────────┬──────────┬──────────┬─────────┐ │
│ │ Agent   │ Workflow │   RAG    │ Model   │ │
│ │ 管理服务│ 引擎服务 │  服务    │ 网关    │ │
│ │         │          │          │ 服务    │ │
│ └─────────┴──────────┴──────────┴─────────┘ │
│ ┌─────────┬──────────┬──────────┬─────────┐ │
│ │  MCP    │   Chat   │ Schedule │ 监控    │ │
│ │ 管理服务│  对话服务│ 调度服务 │ 服务    │ │
│ └─────────┴──────────┴──────────┴─────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 数据层 ───────────────────┐
│ ┌──────────────────┬──────────────────────┐ │
│ │   DynamoDB       │    Vector DB         │ │
│ │ (结构化数据)      │  (向量数据 + 检索)   │ │
│ └──────────────────┴──────────────────────┘ │
│ ┌──────────────────┬──────────────────────┐ │
│ │   S3 对象存储    │    Redis 缓存        │ │
│ │ (文档/模型/日志)  │   (会话/配置)       │ │
│ └──────────────────┴──────────────────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 计算层 ───────────────────┐
│ ┌──────────────────┬──────────────────────┐ │
│ │   MCP Servers    │    LLM Models        │ │
│ │ (工具集群)        │  (多模型支持)        │ │
│ └──────────────────┴──────────────────────┘ │
└─────────────────────────────────────────────┘
```

**架构演进特点**：
- 微服务化拆分，提升系统可扩展性
- 引入模型网关和 RAG 服务
- 增加工作流引擎和可视化编辑器
- 完善监控和可观测性体系
- 支持多种数据存储方案

### 2.3 技术栈选择

| 层级 | 1.0 技术栈 | 2.0 技术栈 | 演进原因 |
|------|-----------|-----------|----------|
| 前端 | React + Ant Design | React + Ant Design + React Flow | 增加工作流可视化能力 |
| 后端 | FastAPI (单体) | FastAPI (微服务) + Kong | 服务拆分 + API 网关 |
| 数据 | DynamoDB | DynamoDB + OpenSearch + S3 | 支持向量检索和文档存储 |
| 缓存 | 无 | Redis Cluster | 提升性能和会话管理 |
| 消息 | 无 | Amazon SQS/SNS | 异步处理和事件驱动 |
| 监控 | 基础日志 | CloudWatch + Grafana + Jaeger | 全链路监控和追踪 |
| 部署 | ECS | ECS/EKS + Terraform | 支持更灵活的容器编排 |

## 3. 核心模块设计（1.0）

### 3.1 Agent 引擎模块

**核心职责**：Agent 生命周期管理、模型调用、上下文维护

```python
# 核心数据结构
@dataclass
class AgentPO:
    agent_id: str
    name: str
    agent_type: Literal["plain", "orchestrator"]  # 普通 | 编排型
    model_config: ModelConfig                     # 模型配置
    system_prompt: str                           # 系统提示词
    tools: List[ToolConfig]                      # 工具配置
    environment: Dict[str, Any]                  # 环境变量
    created_at: datetime
    updated_at: datetime

@dataclass  
class ModelConfig:
    provider: Literal["bedrock", "openai", "anthropic", "litellm", "ollama", "custom"]
    model_name: str
    parameters: Dict[str, Any]  # temperature, max_tokens 等
    api_config: Optional[Dict[str, str]]  # API Key, Endpoint
```

**设计原则**：
- **模型无关性**：通过适配器模式支持多种 LLM 提供商
- **工具可组合性**：Agent 可以灵活组合不同来源的工具
- **环境隔离性**：每个 Agent 拥有独立的运行环境和上下文

**关键实现**：
```python
class AgentExecutor:
    def __init__(self, agent_po: AgentPO):
        self.agent = agent_po
        self.model_client = ModelClientFactory.create(agent_po.model_config)
        self.tool_registry = ToolRegistry(agent_po.tools)
        
    async def execute(self, messages: List[Message]) -> AsyncIterator[Response]:
        # 1. 构建上下文
        context = self._build_context(messages)
        
        # 2. 模型推理
        response = await self.model_client.chat_completion(
            messages=context.messages,
            tools=self.tool_registry.get_schemas(),
            stream=True
        )
        
        # 3. 工具调用处理
        async for chunk in response:
            if chunk.tool_calls:
                results = await self._execute_tools(chunk.tool_calls)
                yield ToolCallResponse(results)
            else:
                yield TextResponse(chunk.content)
```

### 3.2 工具系统模块

**三层工具架构**：

1. **Strands 内置工具**：RAG、文件操作、HTTP 请求、AWS 服务、浏览器自动化、代码解释器
2. **MCP Server 工具**：通过 HTTP 协议动态加载第三方工具
3. **Agent-as-Tool**：将其他 Agent 作为工具进行编排调用

```python
# 工具注册表
class ToolRegistry:
    def __init__(self):
        self.builtin_tools: Dict[str, BuiltinTool] = {}
        self.mcp_tools: Dict[str, MCPTool] = {}
        self.agent_tools: Dict[str, AgentTool] = {}
    
    def register_mcp_server(self, server_config: HttpMCPServer):
        """动态注册 MCP Server 的所有工具"""
        tools = self._discover_mcp_tools(server_config)
        for tool in tools:
            self.mcp_tools[tool.name] = tool
    
    def get_schemas(self) -> List[ToolSchema]:
        """获取所有可用工具的 JSON Schema"""
        return [
            *[tool.schema for tool in self.builtin_tools.values()],
            *[tool.schema for tool in self.mcp_tools.values()], 
            *[tool.schema for tool in self.agent_tools.values()]
        ]

# MCP 工具实现
class MCPTool:
    def __init__(self, server: HttpMCPServer, tool_schema: dict):
        self.server = server
        self.name = tool_schema["name"] 
        self.schema = tool_schema
        
    async def execute(self, parameters: dict) -> dict:
        """调用远程 MCP Server"""
        response = await httpx.post(
            f"{self.server.endpoint}/call/{self.name}",
            json=parameters,
            headers={"Authorization": f"Bearer {self.server.api_key}"}
        )
        return response.json()
```

### 3.3 MCP 管理模块

**核心职责**：MCP Server 注册、工具发现、动态加载、健康检查

```python
@dataclass
class HttpMCPServer:
    server_id: str
    name: str
    endpoint: str           # http://mcp-mysql:8000
    api_key: Optional[str]  # 认证密钥
    description: str
    tags: List[str]         # ["database", "mysql"]
    status: Literal["active", "inactive", "error"]
    last_health_check: datetime
    
class MCPService:
    async def register_server(self, config: HttpMCPServer):
        """注册新的 MCP Server"""
        # 1. 健康检查
        await self._health_check(config)
        
        # 2. 工具发现
        tools = await self._discover_tools(config) 
        
        # 3. 存储配置
        await self.mcp_repository.save(config)
        
        # 4. 更新工具注册表
        self.tool_registry.register_mcp_server(config)
    
    async def _discover_tools(self, server: HttpMCPServer) -> List[dict]:
        """从 MCP Server 发现可用工具"""
        response = await httpx.get(f"{server.endpoint}/tools")
        return response.json()["tools"]

### 3.4 对话系统模块

**核心职责**：WebSocket 连接管理、流式响应、对话持久化

```python
class ChatService:
    def __init__(self):
        self.agent_service = AgentPOService()
        self.chat_repository = ChatRecordRepository()
        
    async def stream_chat(
        self, 
        agent_id: str, 
        messages: List[Message],
        websocket: WebSocket
    ):
        """流式对话处理"""
        # 1. 获取 Agent 配置
        agent = await self.agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(404, "Agent not found")
            
        # 2. 创建对话记录
        chat_record = ChatRecord(
            chat_id=generate_uuid(),
            agent_id=agent_id,
            messages=messages,
            created_at=datetime.now()
        )
        await self.chat_repository.create_chat_record(chat_record)
        
        # 3. 执行 Agent
        executor = AgentExecutor(agent)
        response_chunks = []
        
        async for chunk in executor.execute(messages):
            # 发送到 WebSocket
            await websocket.send_text(chunk.json())
            response_chunks.append(chunk)
            
        # 4. 保存响应记录
        chat_response = ChatResponse(
            response_id=generate_uuid(),
            chat_id=chat_record.chat_id,
            content="".join([c.content for c in response_chunks]),
            tool_calls=[c for c in response_chunks if c.type == "tool_call"],
            created_at=datetime.now()
        )
        await self.chat_repository.create_chat_response(chat_response)
```

### 3.5 调度系统模块

**核心职责**：定时任务管理、EventBridge 集成、Lambda 触发

```python
@dataclass
class AgentSchedule:
    schedule_id: str
    agent_id: str
    name: str
    cron_expression: str     # "0 9 * * MON-FRI"
    input_message: str       # 触发时发送的消息
    enabled: bool
    next_run_time: datetime
    created_at: datetime

class ScheduleService:
    def __init__(self):
        self.eventbridge = boto3.client('events')
        self.lambda_client = boto3.client('lambda')
        
    async def create_schedule(self, schedule: AgentSchedule):
        """创建定时任务"""
        # 1. 创建 EventBridge 规则
        rule_name = f"agent-schedule-{schedule.schedule_id}"
        self.eventbridge.put_rule(
            Name=rule_name,
            ScheduleExpression=f"cron({schedule.cron_expression})",
            State='ENABLED' if schedule.enabled else 'DISABLED',
            Description=f"Schedule for agent {schedule.agent_id}"
        )
        
        # 2. 添加 Lambda 目标
        self.eventbridge.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': '1',
                'Arn': 'arn:aws:lambda:us-east-1:ACCOUNT:function:agentx-scheduler',
                'Input': json.dumps({
                    'agent_id': schedule.agent_id,
                    'message': schedule.input_message,
                    'schedule_id': schedule.schedule_id
                })
            }]
        )
        
        # 3. 保存到数据库
        await self.schedule_repository.save(schedule)

## 4. 2.0 新增模块设计

### 4.1 工作流引擎模块

**设计理念**：借鉴 n8n 的可视化工作流理念，将 Agent 作为可编排的节点，支持复杂业务逻辑的拖拽式构建。

```python
# 工作流节点定义
@dataclass
class WorkflowNode:
    node_id: str
    node_type: Literal["agent", "condition", "delay", "webhook", "transform"]
    config: Dict[str, Any]
    position: Dict[str, float]  # x, y 坐标
    
@dataclass
class WorkflowEdge:
    edge_id: str
    source_node: str
    target_node: str
    condition: Optional[str]  # 条件表达式
    
@dataclass
class Workflow:
    workflow_id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    trigger: WorkflowTrigger
    variables: Dict[str, Any]  # 工作流变量
    created_by: str
    status: Literal["draft", "active", "paused"]
    
# 工作流执行引擎
class WorkflowExecutor:
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.context = WorkflowContext()
        self.node_registry = NodeRegistry()
        
    async def execute(self, trigger_data: dict) -> WorkflowResult:
        """执行工作流"""
        self.context.set_trigger_data(trigger_data)
        
        # 1. 从触发节点开始
        current_nodes = [self.workflow.trigger.start_node]
        
        while current_nodes:
            next_nodes = []
            
            # 2. 并行执行当前层节点
            tasks = [self._execute_node(node_id) for node_id in current_nodes]
            results = await asyncio.gather(*tasks)
            
            # 3. 根据执行结果确定下一层节点
            for i, node_id in enumerate(current_nodes):
                next_nodes.extend(
                    self._get_next_nodes(node_id, results[i])
                )
            
            current_nodes = next_nodes
            
        return WorkflowResult(
            workflow_id=self.workflow.workflow_id,
            status="completed",
            outputs=self.context.get_outputs(),
            execution_time=self.context.get_execution_time()
        )
```

### 4.2 RAG Pipeline 模块

**设计理念**：构建完整的文档处理管道，支持多格式文档解析、分块、向量化、检索和生成。

```python
# RAG 管道定义
@dataclass
class KnowledgeBase:
    kb_id: str
    name: str
    description: str
    embedding_model: str      # "text-embedding-3-large"
    chunk_strategy: ChunkStrategy
    retrieval_config: RetrievalConfig
    created_by: str
    documents_count: int
    
@dataclass  
class Document:
    doc_id: str
    kb_id: str
    name: str
    content_type: str         # "pdf", "docx", "md", "txt"
    file_path: str           # S3 路径
    metadata: Dict[str, Any] # 自定义元数据
    processed_at: datetime
    chunk_count: int

# RAG 服务
class RAGService:
    def __init__(self):
        self.document_parser = DocumentParser()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()  # OpenSearch
        
    async def ingest_document(self, kb_id: str, file_path: str) -> Document:
        """文档摄入管道"""
        # 1. 解析文档
        content = await self.document_parser.parse(file_path)
        
        # 2. 文档分块
        chunks = await self.chunking_service.chunk_document(content.text)
        
        # 3. 批量向量化
        embeddings = await self.embedding_service.embed_batch(
            [chunk.content for chunk in chunks]
        )
        
        # 4. 存储向量
        await self.vector_store.upsert_batch(chunks, embeddings)
        
        return doc
    
    async def hybrid_search(self, kb_id: str, query: str, top_k: int = 5) -> List[SearchResult]:
        """混合检索：向量检索 + BM25"""
        # 1. 向量检索
        query_embedding = await self.embedding_service.embed(query)
        vector_results = await self.vector_store.vector_search(kb_id, query_embedding, top_k * 2)
        
        # 2. 关键词检索  
        keyword_results = await self.vector_store.keyword_search(kb_id, query, top_k * 2)
        
        # 3. 重排序融合
        return self._rerank_results(vector_results, keyword_results, top_k)

### 4.3 模型网关模块

**设计理念**：统一模型接口，支持负载均衡、API Key 轮转、成本优化和智能路由。

```python
# 模型提供商配置
@dataclass
class ModelProvider:
    provider_id: str
    name: str                    # "OpenAI", "Anthropic", "Bedrock"
    base_url: str
    api_keys: List[str]         # 支持多个 API Key 轮转
    models: List[ModelInfo]     # 支持的模型列表
    rate_limits: Dict[str, int] # 速率限制配置
    cost_config: CostConfig     # 计费配置
    status: Literal["active", "inactive", "error"]
    
# 智能路由策略
class ModelRouter:
    def __init__(self):
        self.load_balancer = LoadBalancer()
        self.cost_optimizer = CostOptimizer() 
        self.fallback_manager = FallbackManager()
        
    async def route_request(
        self, 
        request: ChatRequest,
        routing_strategy: str = "cost_optimal"
    ) -> ModelEndpoint:
        """智能路由请求到最优模型"""
        available_models = self._filter_compatible_models(request)
        
        if routing_strategy == "cost_optimal":
            return self.cost_optimizer.select_cheapest(available_models)
        elif routing_strategy == "performance":
            return self._select_fastest(available_models)
        elif routing_strategy == "load_balanced":
            return self.load_balancer.select(available_models)
        else:
            return available_models[0]
```

### 4.4 应用发布模块

**设计理念**：一键将 Agent 或工作流发布为不同形态的应用（API、Chatbot、WebApp）。

```python
# 应用发布配置
@dataclass
class AppDeployment:
    app_id: str
    name: str
    app_type: Literal["api", "chatbot", "webapp"]
    source_type: Literal["agent", "workflow"]
    source_id: str              # agent_id 或 workflow_id
    config: AppConfig
    domain: Optional[str]       # 自定义域名
    auth_config: AuthConfig
    rate_limiting: RateLimitConfig
    status: Literal["deploying", "active", "inactive", "error"]
    created_by: str
    
# 应用发布服务
class AppDeploymentService:
    def __init__(self):
        self.container_service = ECSService()
        self.gateway_service = APIGatewayService()
        self.dns_service = Route53Service()
        
    async def deploy_app(self, deployment: AppDeployment) -> DeploymentResult:
        """部署应用"""
        if deployment.app_type == "api":
            return await self._deploy_api_app(deployment)
        elif deployment.app_type == "chatbot":
            return await self._deploy_chatbot_app(deployment)  
        elif deployment.app_type == "webapp":
            return await self._deploy_webapp(deployment)
```

### 4.5 可观测性模块

**设计理念**：提供全链路追踪、性能监控、成本分析和异常告警能力。

```python
# 调用链追踪
@dataclass
class TraceSpan:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str        # "agent.execute", "tool.call", "model.inference"
    start_time: datetime
    end_time: datetime
    tags: Dict[str, str]      # {"agent_id": "xxx", "model": "gpt-4"}
    logs: List[SpanLog]
    status: Literal["ok", "error", "timeout"]
    
# 监控服务
class ObservabilityService:
    def __init__(self):
        self.tracer = JaegerTracer()
        self.metrics_collector = CloudWatchMetrics()
        self.cost_analyzer = CostAnalyzer()
        
    async def start_trace(self, operation: str, context: dict) -> TraceContext:
        """开始调用链追踪"""
        trace_id = generate_trace_id()
        span = TraceSpan(
            span_id=generate_span_id(),
            trace_id=trace_id,
            operation_name=operation,
            start_time=datetime.now(),
            tags=context
        )
        return TraceContext(trace_id, span)

## 5. 数据模型设计

### 5.1 现有数据模型（1.0）

#### DynamoDB 表设计

**1. AgentTable**
```python
{
    "agent_id": "string",              # 分区键
    "name": "string",
    "agent_type": "plain|orchestrator",
    "model_config": {
        "provider": "string",
        "model_name": "string", 
        "parameters": {}
    },
    "system_prompt": "string",
    "tools": [
        {
            "type": "builtin|mcp|agent",
            "name": "string",
            "config": {}
        }
    ],
    "environment": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

**2. ChatRecordTable** 
```python
{
    "chat_id": "string",               # 分区键
    "agent_id": "string",              # GSI 分区键
    "messages": [
        {
            "role": "user|assistant|system",
            "content": "string",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ],
    "created_at": "2024-01-01T00:00:00Z"
}
```

**3. HttpMCPTable**
```python
{
    "server_id": "string",             # 分区键
    "name": "string", 
    "endpoint": "string",
    "api_key": "string",
    "description": "string",
    "tags": ["string"],
    "status": "active|inactive|error",
    "tools": [                         # 缓存的工具列表
        {
            "name": "string",
            "schema": {}
        }
    ],
    "last_health_check": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### 5.2 新增数据模型（2.0）

#### 工作流相关表

**6. WorkflowTable**
```python
{
    "workflow_id": "string",           # 分区键
    "name": "string",
    "description": "string",
    "definition": {                    # 工作流定义
        "nodes": [
            {
                "node_id": "string",
                "node_type": "agent|condition|delay|webhook",
                "config": {},
                "position": {"x": 100, "y": 200}
            }
        ],
        "edges": [
            {
                "edge_id": "string", 
                "source_node": "string",
                "target_node": "string",
                "condition": "string"
            }
        ]
    },
    "trigger": {
        "type": "manual|webhook|schedule|event",
        "config": {}
    },
    "variables": {},                   # 工作流变量
    "created_by": "string",
    "status": "draft|active|paused",
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### RAG 相关表

**8. KnowledgeBaseTable**
```python
{
    "kb_id": "string",                 # 分区键
    "name": "string",
    "description": "string", 
    "embedding_model": "text-embedding-3-large",
    "chunk_strategy": {
        "type": "fixed|semantic|recursive",
        "chunk_size": 1000,
        "chunk_overlap": 200
    },
    "retrieval_config": {
        "top_k": 5,
        "similarity_threshold": 0.7,
        "hybrid_search": true
    },
    "created_by": "string",
    "documents_count": 0,
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### 模型网关相关表

**10. ModelProviderTable**
```python
{
    "provider_id": "string",           # 分区键
    "name": "OpenAI|Anthropic|Bedrock",
    "base_url": "https://api.openai.com/v1",
    "api_keys": [
        {
            "key_id": "string",
            "masked_key": "sk-***abc",
            "status": "active|inactive|expired",
            "rate_limit_remaining": 1000,
            "last_used_at": "2024-01-01T00:00:00Z"
        }
    ],
    "models": [
        {
            "model_id": "gpt-4o",
            "display_name": "GPT-4o",
            "input_cost_per_1k": 0.005,
            "output_cost_per_1k": 0.015,
            "max_tokens": 128000,
            "capabilities": ["text", "image", "function_calling"]
        }
    ],
    "status": "active|inactive|error",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### 5.3 数据存储方案

#### OpenSearch 向量存储
```json
{
  "mappings": {
    "properties": {
      "chunk_id": {"type": "keyword"},
      "kb_id": {"type": "keyword"},
      "doc_id": {"type": "keyword"}, 
      "content": {"type": "text", "analyzer": "ik_max_word"},
      "embedding": {
        "type": "dense_vector",
        "dims": 1536
      },
      "metadata": {"type": "object"},
      "position": {"type": "integer"},
      "created_at": {"type": "date"}
    }
  }
}
```

#### Redis 缓存设计
```python
# 缓存 Key 命名规范
CACHE_KEYS = {
    "agent_config": "agent:{agent_id}:config",
    "mcp_tools": "mcp:{server_id}:tools",
    "model_routing": "model:routing:{hash}",
    "workflow_definition": "workflow:{workflow_id}:definition",
    "rag_results": "rag:{kb_id}:{query_hash}",
    "user_session": "session:{user_id}:{session_id}"
}

## 6. 部署架构

### 6.1 1.0 部署架构（当前）

```
┌─────────────────── 用户流量 ───────────────────┐
│  Internet → CloudFront → ALB → ECS Tasks     │
└──────────────────────────────────────────────┘

AWS 资源拓扑：
┌─────────────────────────────────────────────┐
│                  VPC                        │
│  ┌─────────────────┬─────────────────────┐  │
│  │  Public Subnet  │  Private Subnet     │  │
│  │  ┌───────────┐  │  ┌───────────────┐  │  │
│  │  │    ALB    │  │  │  ECS Cluster  │  │  │
│  │  └───────────┘  │  │  ┌─────────┐  │  │  │
│  │                 │  │  │FastAPI  │  │  │  │
│  │                 │  │  │Backend  │  │  │  │
│  └─────────────────┴─────────────────────┘  │
│                                             │
│  ┌─────────────────────────────────────────┐ │
│  │              DynamoDB                   │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 6.2 2.0 目标架构（微服务）

```
┌─────────────────── 网关层 ───────────────────┐
│              Kong API Gateway                │
│  认证 │ 限流 │ 路由 │ 监控 │ 日志 │ CORS      │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 服务层 ───────────────────┐
│ ┌─────────┬──────────┬──────────┬─────────┐ │
│ │ Agent   │ Workflow │   RAG    │ Model   │ │
│ │ Service │ Service  │ Service  │Gateway  │ │
│ └─────────┴──────────┴──────────┴─────────┘ │
└─────────────────────────────────────────────┘
                         │
┌─────────────────── 数据层 ───────────────────┐
│ ┌──────────────────┬──────────────────────┐ │
│ │   DynamoDB       │    OpenSearch        │ │
│ │ (结构化数据)      │ (向量 + 全文检索)     │ │
│ └──────────────────┴──────────────────────┘ │
└─────────────────────────────────────────────┘
```

## 7. 开发路线图

### 7.1 阶段规划

#### Q1 2024：基础平台稳定（1.0 完善）

**P0 - 核心稳定性**
- [ ] Agent 执行引擎优化（错误处理、重试机制）
- [ ] MCP Server 健康检查和自动恢复
- [ ] API 限流和安全认证
- [ ] 完整的单元测试和集成测试

**P1 - 功能增强**
- [ ] Agent 版本管理和回滚
- [ ] 批量 Agent 操作（导入/导出）
- [ ] 对话历史搜索和过滤
- [ ] 基础监控和日志

#### Q2 2024：工作流引擎（2.0 启动）

**P0 - 工作流核心**
- [ ] 可视化工作流编辑器（React Flow）
- [ ] 基础节点类型（Agent、条件、延迟、Webhook）
- [ ] 工作流执行引擎
- [ ] 节点状态跟踪和错误处理

**P1 - 工作流增强**
- [ ] 高级节点类型（循环、分支、聚合）
- [ ] 工作流模板和分享
- [ ] 变量传递和上下文管理

#### Q3 2024：RAG 系统（知识驱动）

**P0 - RAG 核心**
- [ ] 文档上传和解析（PDF、Word、Markdown）
- [ ] 文档分块和向量化
- [ ] OpenSearch 向量存储集成
- [ ] 混合检索（向量 + 关键词）

**P1 - RAG 增强**
- [ ] 多种 Embedding 模型支持
- [ ] 智能分块策略（语义分段）
- [ ] 知识库管理界面

#### Q4 2024：模型网关和应用发布

**P0 - 模型网关**
- [ ] 多提供商模型统一接口
- [ ] 智能路由和负载均衡
- [ ] API Key 管理和轮转
- [ ] 成本统计和优化

**P1 - 应用发布**
- [ ] Agent/工作流一键发布为 API
- [ ] Chatbot 应用生成
- [ ] 自定义域名和 SSL

## 8. 技术决策记录

### 8.1 架构决策

**ADR-001: 选择 FastAPI 作为后端框架**
- **状态**：已采用
- **决策**：使用 FastAPI 替代 Django/Flask
- **理由**：
  - 原生异步支持，适合 AI 推理的 I/O 密集场景
  - 自动 API 文档生成（Swagger/OpenAPI）
  - 类型提示和数据验证
  - 性能优秀，社区活跃

**ADR-002: 选择 DynamoDB 作为主数据库**
- **状态**：已采用  
- **决策**：使用 DynamoDB 而非关系型数据库
- **理由**：
  - 无服务器，自动扩展，运维成本低
  - 与 AWS 生态集成良好
  - 支持文档型数据结构，适合 Agent 配置存储
  - 高可用性和持久性保证

**ADR-003: 采用 MCP 协议进行工具集成**
- **状态**：已采用
- **决策**：基于 MCP (Model Context Protocol) 标准化工具接口
- **理由**：
  - 行业标准，避免厂商锁定
  - 支持动态工具发现和加载
  - 社区生态丰富

### 8.2 技术选型

**ADR-004: 容器化部署（ECS vs EKS）**
- **状态**：当前 ECS，考虑迁移 EKS
- **决策**：1.0 使用 ECS Fargate，2.0 考虑 EKS
- **理由**：
  - ECS：简单易用，AWS 托管，运维成本低
  - EKS：更强的容器编排能力，适合微服务架构

**ADR-005: 向量数据库选择 OpenSearch**
- **状态**：计划采用
- **决策**：使用 Amazon OpenSearch 进行向量存储和检索
- **理由**：
  - 同时支持向量检索和全文搜索
  - AWS 托管服务，运维简单
  - 与现有 AWS 技术栈集成

### 8.3 安全决策

**ADR-006: API 认证策略**
- **状态**：设计中
- **决策**：采用 JWT + API Key 混合认证
- **方案**：
  - 用户登录：JWT Token (15min) + Refresh Token (30天)
  - 服务间调用：mTLS 或 AWS IAM
  - 第三方集成：API Key + 签名验证

---

## 总结

AgentX 平台设计遵循"**简单可用、逐步演进**"的原则，1.0 版本专注于核心功能的稳定性和可用性，2.0 版本引入工作流、RAG、模型网关等企业级功能，最终目标是打造一个完整的 AI 应用开发和运营平台。

**核心设计理念**：
- **标准化**：基于 MCP 协议构建开放生态
- **可观测**：全链路监控，数据驱动优化
- **易用性**：降低 AI 应用开发门槛
- **企业级**：满足生产环境的可靠性要求

技术栈的选择既考虑了现有团队能力，也为未来扩展预留了空间。通过渐进式的架构演进，确保平台能够支撑业务的长期发展。
```
```
```
```
```