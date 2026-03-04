import React from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { StopOutlined } from '@ant-design/icons';
import '../workflow.css';

export const EndNode: React.FC<NodeProps> = ({ selected }) => {
  return (
    <div className={`workflow-node end-node${selected ? ' selected' : ''}`}>
      <Handle
        type="target"
        position={Position.Left}
      />
      <div className="node-content">
        <StopOutlined className="node-icon" />
        <span className="node-label">结束</span>
      </div>
    </div>
  );
};
