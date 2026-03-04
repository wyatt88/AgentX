import type { GetProp } from 'antd';
import type { Attachments, Prompts } from '@ant-design/x';

export type BubbleDataType = {
  role: string;
  content: string;
};

export type ConversationItemType = {
  key: string;
  label: string;
  group: string;
};

export type MessageHistoryType = Record<string, Array<{
  message: BubbleDataType;
  status?: 'loading' | 'done' | 'error';
}>>;

export type AttachedFileType = GetProp<typeof Attachments, 'items'>;
export type PromptsItemType = GetProp<typeof Prompts, 'items'>;

// Agent Event Types
export interface ToolMetrics {
  tool: {
    toolUseId: string;
    name: string;
    input: Record<string, unknown>;
  };
  call_count: number;
  success_count: number;
  error_count: number;
  total_time: number;
}

export interface EventLoopMetrics {
  cycle_count: number;
  tool_metrics: Record<string, ToolMetrics>;
  cycle_durations: number[];
  accumulated_usage: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
  accumulated_metrics: {
    latencyMs: number;
  };
}

export interface TextGenerationEvent {
  data: string;
  delta: {
    text: string;
  };
  event_loop_metrics: EventLoopMetrics;
  event_loop_cycle_id: string;
  request_state: Record<string, unknown>;
  event_loop_parent_cycle_id?: string;
}

export interface ToolEvent {
  delta: {
    toolUse: {
      input: string;
    };
  };
  current_tool_use: {
    toolUseId: string;
    name: string;
    input: Record<string, unknown>;
  };
  event_loop_metrics: EventLoopMetrics;
  event_loop_cycle_id: string;
  request_state: Record<string, unknown>;
  event_loop_parent_cycle_id?: string;
}

export interface ContentBlockDelta {
  delta: {
    text?: string;
    toolUse?: {
      input: string;
    };
  };
  contentBlockIndex: number;
}

export interface ContentBlockStart {
  start: {
    toolUse?: {
      toolUseId: string;
      name: string;
    };
  };
  contentBlockIndex: number;
}

export interface ContentBlockStop {
  contentBlockIndex: number;
}

export interface MessageStart {
  role: string;
}

export interface MessageStop {
  stopReason: string;
}

export interface MetadataEvent {
  usage: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
  metrics: {
    latencyMs: number;
  };
}

export interface EventType {
  messageStart?: MessageStart;
  messageStop?: MessageStop;
  contentBlockStart?: ContentBlockStart;
  contentBlockDelta?: ContentBlockDelta;
  contentBlockStop?: ContentBlockStop;
  metadata?: MetadataEvent;
}

export interface EventEvent {
  event: EventType;
}

export interface MessageContent {
  text?: string;
  toolUse?: {
    toolUseId: string;
    name: string;
    input: Record<string, unknown>;
  };
  toolResult?: {
    status: string;
    content: Array<Record<string, unknown>>;
    toolUseId: string;
  };
}

export interface Message {
  role: string;
  content: MessageContent[];
}

export interface MessageEvent {
  message: Message;
}

export interface InitEvent {
  init_event_loop?: boolean;
  start?: boolean;
  start_event_loop?: boolean;
}

export interface LifecycleEvent {
  force_stop?: boolean;
  force_stop_reason?: string;
}

export interface ReasoningEvent {
  reasoning: boolean;
  reasoningText: string;
  reasoning_signature?: string;
}

export type AgentEvent = 
  | TextGenerationEvent 
  | ToolEvent 
  | EventEvent
  | MessageEvent
  | InitEvent
  | LifecycleEvent 
  | ReasoningEvent;

// Workflow types
export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'published' | 'archived';
  definition: WorkflowDefinition;
  trigger_type: string;
  trigger_config: any;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkflowReq {
  name: string;
  description: string;
  definition?: WorkflowDefinition;
  trigger_type?: string;
  trigger_config?: any;
}

export interface UpdateWorkflowReq {
  name?: string;
  description?: string;
  status?: 'draft' | 'published' | 'archived';
  definition?: WorkflowDefinition;
  trigger_type?: string;
  trigger_config?: any;
}

// Model Provider types
export interface ModelProvider {
  id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  models: string[];
  is_default: boolean;
  status: string;
}

export interface CreateModelProviderReq {
  name: string;
  type: string;
  config: Record<string, any>;
  models: string[];
  is_default?: boolean;
}

export interface UpdateModelProviderReq {
  name?: string;
  type?: string;
  config?: Record<string, any>;
  models?: string[];
  is_default?: boolean;
}

// MCP Server extended types
export interface MCPServerTool {
  name: string;
  description: string;
  input_schema?: Record<string, any>;
}

export interface MCPHealthCheckResult {
  server_id: string;
  status: 'running' | 'stopped' | 'error';
  message?: string;
  checked_at: string;
}

// Workflow execution types
export type WorkflowExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface WorkflowNodeExecution {
  node_id: string;
  node_type: string;
  status: WorkflowExecutionStatus;
  started_at?: string;
  completed_at?: string;
  output?: Record<string, any>;
  error?: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: WorkflowExecutionStatus;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  node_executions: WorkflowNodeExecution[];
  started_at: string;
  completed_at?: string;
  error?: string;
}

// Helper function to determine event type
export const getEventType = (event: AgentEvent): 'text' | 'tool' | 'event' | 'message' | 'init' | 'lifecycle' | 'reasoning' => {
  if ('data' in event) return 'text';
  if ('current_tool_use' in event) return 'tool';
  if ('event' in event) return 'event';
  if ('message' in event) return 'message';
  if ('init_event_loop' in event || 'start' in event || 'start_event_loop' in event) return 'init';
  if ('reasoning' in event) return 'reasoning';
  return 'lifecycle';
};
