import React from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { CodeOutlined } from '@ant-design/icons';
import type { CodeNodeData } from '../types';
import '../workflow.css';

export const CodeNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as CodeNodeData;

  const codePreview = nodeData.code
    ? nodeData.code.length > 40
      ? nodeData.code.slice(0, 40) + '...'
      : nodeData.code
    : '无代码';

  return (
    <div className={`workflow-node code-node${selected ? ' selected' : ''}`}>
      <Handle
        type="target"
        position={Position.Left}
      />
      <div className="node-header">
        <CodeOutlined />
        <span>代码</span>
        {nodeData.language && (
          <span className="lang-badge">{nodeData.language}</span>
        )}
      </div>
      <div className="node-body">
        {codePreview}
      </div>
      <Handle
        type="source"
        position={Position.Right}
      />
    </div>
  );
};
