import type { Node, Edge } from '@xyflow/react';

// ==================== Workflow Types ====================

export type WorkflowStatus = 'draft' | 'published' | 'archived';

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  definition: WorkflowDefinition;
  trigger_type: string;
  trigger_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

// ==================== Node Types ====================

export type WorkflowNodeType = 'start' | 'agent' | 'condition' | 'code' | 'end';

export interface StartNodeData {
  label: string;
  [key: string]: unknown;
}

export interface AgentNodeData {
  label: string;
  agent_id?: string;
  agent_name?: string;
  model_id?: string;
  input_mapping?: Record<string, string>;
  [key: string]: unknown;
}

export interface ConditionNodeData {
  label: string;
  expression?: string;
  [key: string]: unknown;
}

export interface CodeNodeData {
  label: string;
  code?: string;
  language?: string;
  [key: string]: unknown;
}

export interface EndNodeData {
  label: string;
  output_key?: string;
  [key: string]: unknown;
}

export type WorkflowNodeData =
  | StartNodeData
  | AgentNodeData
  | ConditionNodeData
  | CodeNodeData
  | EndNodeData;

// ==================== ReactFlow Node/Edge with our data ====================

export type FlowNode = Node<WorkflowNodeData, WorkflowNodeType>;
export type FlowEdge = Edge;

// ==================== Color Spec (Appendix A) ====================

export const NODE_COLORS: Record<WorkflowNodeType, string> = {
  start: '#52c41a',     // 绿
  agent: '#1890ff',     // 蓝
  condition: '#faad14', // 黄
  code: '#722ed1',      // 紫
  end: '#ff4d4f',       // 红
};

// ==================== Node Panel Item ====================

export interface NodePanelItem {
  type: WorkflowNodeType;
  label: string;
  icon: string;
  description: string;
  color: string;
}

export const NODE_PANEL_ITEMS: NodePanelItem[] = [
  {
    type: 'start',
    label: '开始',
    icon: '▶',
    description: '工作流入口节点',
    color: NODE_COLORS.start,
  },
  {
    type: 'agent',
    label: 'Agent',
    icon: '🤖',
    description: '调用 AI Agent 处理任务',
    color: NODE_COLORS.agent,
  },
  {
    type: 'condition',
    label: '条件分支',
    icon: '⚡',
    description: '根据条件走不同分支',
    color: NODE_COLORS.condition,
  },
  {
    type: 'code',
    label: '代码',
    icon: '</>',
    description: '执行自定义代码逻辑',
    color: NODE_COLORS.code,
  },
  {
    type: 'end',
    label: '结束',
    icon: '⏹',
    description: '工作流结束节点',
    color: NODE_COLORS.end,
  },
];
