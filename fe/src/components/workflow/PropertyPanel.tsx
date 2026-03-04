import React, { useEffect, useState } from 'react';
import {
  Form,
  Input,
  Select,
  Typography,
  Divider,
  Empty,
} from 'antd';
import type { Node } from '@xyflow/react';
import { agentAPI } from '../../services/api';
import type { Agent } from '../../services/api';
import type {
  WorkflowNodeType,
  WorkflowNodeData,
} from './types';
import { NODE_COLORS } from './types';

const { TextArea } = Input;
const { Text } = Typography;
const { Option } = Select;

interface PropertyPanelProps {
  selectedNode: Node | null;
  onNodeDataChange: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
}

export const PropertyPanel: React.FC<PropertyPanelProps> = ({
  selectedNode,
  onNodeDataChange,
}) => {
  const [form] = Form.useForm();
  const [agents, setAgents] = useState<Agent[]>([]);

  // Fetch agents list for Agent node config
  useEffect(() => {
    agentAPI.getAgents().then(setAgents).catch(console.error);
  }, []);

  // Sync form when selected node changes
  useEffect(() => {
    if (selectedNode) {
      form.setFieldsValue(selectedNode.data);
    } else {
      form.resetFields();
    }
  }, [selectedNode, form]);

  if (!selectedNode) {
    return (
      <div
        style={{
          width: 300,
          borderLeft: '1px solid #f0f0f0',
          background: '#fafafa',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
        }}
      >
        <Empty description="选择节点查看属性" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    );
  }

  const nodeType = selectedNode.type as WorkflowNodeType;
  const color = NODE_COLORS[nodeType] || '#999';

  const handleValuesChange = (_: unknown, allValues: Record<string, unknown>) => {
    onNodeDataChange(selectedNode.id, allValues);
  };

  const renderStartForm = () => (
    <Form.Item label="节点名称" name="label">
      <Input placeholder="开始" />
    </Form.Item>
  );

  const renderAgentForm = () => (
    <>
      <Form.Item label="节点名称" name="label">
        <Input placeholder="Agent 节点" />
      </Form.Item>
      <Form.Item label="选择 Agent" name="agent_id">
        <Select
          placeholder="请选择 Agent"
          allowClear
          onChange={(value: string) => {
            const agent = agents.find((a) => a.id === value);
            if (agent) {
              form.setFieldsValue({
                agent_name: agent.display_name || agent.name,
                model_id: agent.model_id,
              });
              onNodeDataChange(selectedNode.id, {
                ...form.getFieldsValue(),
                agent_id: value,
                agent_name: agent.display_name || agent.name,
                model_id: agent.model_id,
              });
            }
          }}
        >
          {agents.map((agent) => (
            <Option key={agent.id} value={agent.id}>
              {agent.display_name || agent.name}
            </Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item label="Agent 名称" name="agent_name">
        <Input disabled placeholder="自动填充" />
      </Form.Item>
      <Form.Item label="模型" name="model_id">
        <Input disabled placeholder="自动填充" />
      </Form.Item>
      <Form.Item label="输入映射 (JSON)" name="input_mapping">
        <TextArea rows={3} placeholder='{"key": "{{prev.output}}"}' />
      </Form.Item>
    </>
  );

  const renderConditionForm = () => (
    <>
      <Form.Item label="节点名称" name="label">
        <Input placeholder="条件分支" />
      </Form.Item>
      <Form.Item label="条件表达式" name="expression">
        <TextArea
          rows={3}
          placeholder="例如: data.score > 80"
        />
      </Form.Item>
    </>
  );

  const renderCodeForm = () => (
    <>
      <Form.Item label="节点名称" name="label">
        <Input placeholder="代码节点" />
      </Form.Item>
      <Form.Item label="语言" name="language">
        <Select placeholder="选择语言" defaultValue="python">
          <Option value="python">Python</Option>
          <Option value="javascript">JavaScript</Option>
        </Select>
      </Form.Item>
      <Form.Item label="代码" name="code">
        <TextArea
          rows={8}
          placeholder="def handler(data):&#10;    return data"
          style={{ fontFamily: 'monospace', fontSize: 12 }}
        />
      </Form.Item>
    </>
  );

  const renderEndForm = () => (
    <>
      <Form.Item label="节点名称" name="label">
        <Input placeholder="结束" />
      </Form.Item>
      <Form.Item label="输出 Key" name="output_key">
        <Input placeholder="result" />
      </Form.Item>
    </>
  );

  const formRenderers: Record<WorkflowNodeType, () => React.ReactNode> = {
    start: renderStartForm,
    agent: renderAgentForm,
    condition: renderConditionForm,
    code: renderCodeForm,
    end: renderEndForm,
  };

  const renderForm = formRenderers[nodeType];

  return (
    <div
      style={{
        width: 300,
        borderLeft: '1px solid #f0f0f0',
        background: '#fafafa',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '12px 16px 8px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: color,
          }}
        />
        <span style={{ fontWeight: 600, fontSize: 14 }}>属性配置</span>
        <Text type="secondary" style={{ marginLeft: 'auto', fontSize: 12 }}>
          {nodeType}
        </Text>
      </div>
      <Divider style={{ margin: '0 0 12px' }} />
      <div style={{ flex: 1, overflow: 'auto', padding: '0 16px 16px' }}>
        <Form
          form={form}
          layout="vertical"
          size="small"
          onValuesChange={handleValuesChange}
          initialValues={selectedNode.data}
        >
          {renderForm ? renderForm() : null}
        </Form>
        <Divider style={{ margin: '8px 0' }} />
        <Text type="secondary" style={{ fontSize: 11 }}>
          ID: {selectedNode.id}
        </Text>
      </div>
    </div>
  );
};
