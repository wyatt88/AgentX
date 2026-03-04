import React from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { RobotOutlined } from '@ant-design/icons';
import type { AgentNodeData } from '../types';
import '../workflow.css';

export const AgentNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as AgentNodeData;

  return (
    <div className={`workflow-node agent-node${selected ? ' selected' : ''}`}>
      <Handle
        type="target"
        position={Position.Left}
      />
      <div className="node-header">
        <RobotOutlined />
        <span>Agent</span>
      </div>
      <div className="node-body">
        <div className="node-title">
          {nodeData.agent_name || '未选择 Agent'}
        </div>
        {nodeData.model_id && (
          <div className="node-subtitle">
            {nodeData.model_id}
          </div>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
      />
    </div>
  );
};
