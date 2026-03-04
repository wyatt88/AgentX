import React, { useCallback, useRef, useState, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
} from '@xyflow/react';
import type {
  Connection,
  Node,
  Edge,
  ReactFlowInstance,
  NodeTypes,
  OnConnect,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './workflow.css';

import { Button, Space, Input, message, Tooltip, Tag } from 'antd';
import {
  SaveOutlined,
  SendOutlined,
  RollbackOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

import { StartNode, AgentNode, ConditionNode, CodeNode, EndNode } from './nodes';
import { NodePanel } from './NodePanel';
import { PropertyPanel } from './PropertyPanel';
import type {
  WorkflowNodeType,
  WorkflowNodeData,
  Workflow,
  WorkflowNode,
  WorkflowEdge,
} from './types';
import { NODE_COLORS } from './types';

const BASE_URL = '/api';

// ==================== Custom node type registry ====================

const nodeTypes: NodeTypes = {
  start: StartNode,
  agent: AgentNode,
  condition: ConditionNode,
  code: CodeNode,
  end: EndNode,
};

// ==================== Defaults for new nodes by type ====================

const DEFAULT_NODE_DATA: Record<WorkflowNodeType, Record<string, unknown>> = {
  start: { label: '开始' },
  agent: { label: 'Agent', agent_id: '', agent_name: '', model_id: '' },
  condition: { label: '条件分支', expression: '' },
  code: { label: '代码', code: '', language: 'python' },
  end: { label: '结束', output_key: 'result' },
};

// ==================== Helpers ====================

let nodeIdCounter = 0;
const nextNodeId = (): string => `node_${Date.now()}_${nodeIdCounter++}`;

// ==================== Local API (mirrors workflowAPI until services/api.ts is extended) ====================

const wfAPI = {
  get: async (id: string): Promise<Workflow | null> => {
    try {
      const res = await axios.get(`${BASE_URL}/workflow/get/${id}`);
      return res.data;
    } catch (err) {
      console.error('Error loading workflow:', err);
      return null;
    }
  },
  update: async (
    id: string,
    payload: { name?: string; description?: string; definition?: { nodes: WorkflowNode[]; edges: WorkflowEdge[] }; status?: string },
  ): Promise<boolean> => {
    try {
      await axios.put(`${BASE_URL}/workflow/update/${id}`, payload);
      return true;
    } catch (err) {
      console.error('Error saving workflow:', err);
      return false;
    }
  },
  execute: (id: string): Promise<Response> => {
    return fetch(`${BASE_URL}/workflow/execute/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({}),
    });
  },
};

// ==================== Inner Canvas (needs ReactFlowProvider wrapper) ====================

const WorkflowCanvasInner: React.FC = () => {
  const { id: workflowId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);

  // ReactFlow state
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Selection
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Workflow metadata
  const [workflowName, setWorkflowName] = useState('未命名工作流');
  const [workflowStatus, setWorkflowStatus] = useState<string>('draft');
  const [saving, setSaving] = useState(false);

  // ---- Load workflow from backend ----
  useEffect(() => {
    if (!workflowId) return;
    (async () => {
      const wf = await wfAPI.get(workflowId);
      if (wf) {
        setWorkflowName(wf.name);
        setWorkflowStatus(wf.status);
        if (wf.definition) {
          const loadedNodes: Node[] = (wf.definition.nodes || []).map((n) => ({
            id: n.id,
            type: n.type,
            position: n.position,
            data: n.data,
          }));
          const loadedEdges: Edge[] = (wf.definition.edges || []).map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            label: e.label,
            animated: true,
            style: { stroke: '#999' },
          }));
          setNodes(loadedNodes);
          setEdges(loadedEdges);
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  // ---- Connection handler ----
  const onConnect: OnConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            animated: true,
            style: { stroke: '#999' },
          },
          eds,
        ),
      );
    },
    [setEdges],
  );

  // ---- Node selection ----
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
    },
    [],
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Keep selectedNode in sync with nodes array
  useEffect(() => {
    if (selectedNode) {
      const current = nodes.find((n) => n.id === selectedNode.id);
      if (current && current !== selectedNode) {
        setSelectedNode(current);
      }
    }
  }, [nodes, selectedNode]);

  // ---- Drop handler (from NodePanel drag) ----
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const nodeType = event.dataTransfer.getData(
        'application/reactflow-type',
      ) as WorkflowNodeType;
      if (!nodeType || !rfInstance) return;

      const position = rfInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: nextNodeId(),
        type: nodeType,
        position,
        data: { ...DEFAULT_NODE_DATA[nodeType] },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [rfInstance, setNodes],
  );

  // ---- Property panel data change ----
  const handleNodeDataChange = useCallback(
    (nodeId: string, data: Partial<WorkflowNodeData>) => {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === nodeId) {
            return { ...n, data: { ...n.data, ...data } };
          }
          return n;
        }),
      );
    },
    [setNodes],
  );

  // ---- Save ----
  const handleSave = useCallback(async () => {
    if (!workflowId) return;
    setSaving(true);
    const definition: { nodes: WorkflowNode[]; edges: WorkflowEdge[] } = {
      nodes: nodes.map((n) => ({
        id: n.id,
        type: (n.type ?? 'start') as WorkflowNodeType,
        position: n.position,
        data: n.data as Record<string, unknown>,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: typeof e.label === 'string' ? e.label : undefined,
      })),
    };
    const ok = await wfAPI.update(workflowId, { name: workflowName, definition });
    setSaving(false);
    if (ok) {
      message.success('保存成功');
    } else {
      message.error('保存失败');
    }
  }, [workflowId, workflowName, nodes, edges]);

  // ---- Publish ----
  const handlePublish = useCallback(async () => {
    if (!workflowId) return;
    // Save first, then change status
    await handleSave();
    const ok = await wfAPI.update(workflowId, { status: 'published' });
    if (ok) {
      setWorkflowStatus('published');
      message.success('已发布');
    }
  }, [workflowId, handleSave]);

  // ---- Execute ----
  const handleExecute = useCallback(async () => {
    if (!workflowId) return;
    try {
      message.info('工作流开始执行');
      await wfAPI.execute(workflowId);
    } catch {
      message.error('执行失败');
    }
  }, [workflowId]);

  // ---- MiniMap node color ----
  const miniMapNodeColor = useCallback((node: Node) => {
    return NODE_COLORS[(node.type as WorkflowNodeType) || 'start'] || '#ccc';
  }, []);

  // Memoize nodeTypes to avoid ReactFlow warning about changing reference
  const stableNodeTypes = useMemo(() => nodeTypes, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* ===== Top toolbar ===== */}
      <div
        style={{
          height: 48,
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          gap: 12,
          background: '#fff',
          flexShrink: 0,
        }}
      >
        <Tooltip title="返回列表">
          <Button icon={<RollbackOutlined />} type="text" onClick={() => navigate('/workflows')} />
        </Tooltip>

        <Input
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          variant="borderless"
          style={{ fontWeight: 600, fontSize: 15, maxWidth: 300 }}
        />

        <Tag color={workflowStatus === 'published' ? 'success' : 'default'}>
          {workflowStatus === 'published' ? '已发布' : '草稿'}
        </Tag>

        <div style={{ flex: 1 }} />

        <Space>
          <Button icon={<SaveOutlined />} loading={saving} onClick={handleSave}>
            保存
          </Button>
          <Button icon={<CloudUploadOutlined />} onClick={handlePublish}>
            发布
          </Button>
          <Button type="primary" icon={<SendOutlined />} onClick={handleExecute}>
            执行
          </Button>
        </Space>
      </div>

      {/* ===== Three-column body ===== */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: Node panel */}
        <NodePanel />

        {/* Center: ReactFlow canvas */}
        <div ref={reactFlowWrapper} style={{ flex: 1, position: 'relative' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onInit={setRfInstance}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={stableNodeTypes}
            fitView
            deleteKeyCode={['Backspace', 'Delete']}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={16} size={1} />
            <Controls />
            <MiniMap
              nodeColor={miniMapNodeColor}
              style={{ border: '1px solid #e8e8e8', borderRadius: 4 }}
            />
          </ReactFlow>
        </div>

        {/* Right: Property panel */}
        <PropertyPanel
          selectedNode={selectedNode}
          onNodeDataChange={handleNodeDataChange}
        />
      </div>
    </div>
  );
};

// ==================== Exported wrapper with provider ====================

export const WorkflowCanvas: React.FC = () => (
  <ReactFlowProvider>
    <WorkflowCanvasInner />
  </ReactFlowProvider>
);
