import React from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { PlayCircleOutlined } from '@ant-design/icons';
import '../workflow.css';

export const StartNode: React.FC<NodeProps> = ({ selected }) => {
  return (
    <div className={`workflow-node start-node${selected ? ' selected' : ''}`}>
      <div className="node-content">
        <PlayCircleOutlined className="node-icon" />
        <span className="node-label">开始</span>
      </div>
      <Handle
        type="source"
        position={Position.Right}
      />
    </div>
  );
};
