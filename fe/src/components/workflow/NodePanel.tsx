import React from 'react';
import { Typography, Divider } from 'antd';
import { NODE_PANEL_ITEMS } from './types';
import type { WorkflowNodeType } from './types';

const { Text } = Typography;

export const NodePanel: React.FC = () => {
  const onDragStart = (
    event: React.DragEvent<HTMLDivElement>,
    nodeType: WorkflowNodeType,
  ) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      style={{
        width: 200,
        borderRight: '1px solid #f0f0f0',
        background: '#fafafa',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      <div style={{ padding: '12px 16px 8px', fontWeight: 600, fontSize: 14 }}>
        节点面板
      </div>
      <Divider style={{ margin: '0 0 8px' }} />
      <div style={{ flex: 1, overflow: 'auto', padding: '0 12px 12px' }}>
        {NODE_PANEL_ITEMS.map((item) => (
          <div
            key={item.type}
            draggable
            onDragStart={(e) => onDragStart(e, item.type)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 12px',
              marginBottom: 8,
              background: '#fff',
              borderRadius: 8,
              border: '1px solid #e8e8e8',
              cursor: 'grab',
              transition: 'all 0.2s ease',
              userSelect: 'none',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.borderColor = item.color;
              (e.currentTarget as HTMLDivElement).style.boxShadow = `0 2px 8px ${item.color}22`;
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.borderColor = '#e8e8e8';
              (e.currentTarget as HTMLDivElement).style.boxShadow = 'none';
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 6,
                background: `${item.color}15`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 16,
                flexShrink: 0,
              }}
            >
              {item.icon}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 500, fontSize: 13, color: '#333' }}>
                {item.label}
              </div>
              <Text
                type="secondary"
                style={{ fontSize: 11 }}
                ellipsis={{ tooltip: item.description }}
              >
                {item.description}
              </Text>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
