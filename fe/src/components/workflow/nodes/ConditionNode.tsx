import React from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { BranchesOutlined } from '@ant-design/icons';
import type { ConditionNodeData } from '../types';
import '../workflow.css';

export const ConditionNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as ConditionNodeData;

  return (
    <div className={`condition-node-wrapper${selected ? ' selected' : ''}`}>
      <div className="condition-node-diamond" />
      <div className="condition-node-content">
        <BranchesOutlined className="node-icon" />
        <div className="node-label">条件分支</div>
        <div className="node-expr">
          {nodeData.expression || '未设置条件'}
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Left}
      />
      {/* True output (top-right) */}
      <Handle
        type="source"
        position={Position.Right}
        id="true"
        style={{ top: '30%' }}
      />
      {/* False output (bottom-right) */}
      <Handle
        type="source"
        position={Position.Right}
        id="false"
        style={{ top: '70%' }}
      />
    </div>
  );
};
