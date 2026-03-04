import React, { useEffect, useState } from 'react';
import {
  Card,
  Typography,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Tag,
  Badge,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { useModelStore } from '../../store';
import type { ModelProvider as ModelProviderType } from '../../types';

const { Title, Paragraph } = Typography;

const PROVIDER_TYPES = [
  { value: 'bedrock', label: 'AWS Bedrock', color: 'orange' },
  { value: 'openai', label: 'OpenAI', color: 'green' },
  { value: 'ollama', label: 'Ollama', color: 'purple' },
  { value: 'litellm', label: 'LiteLLM', color: 'cyan' },
  { value: 'custom', label: 'Custom', color: 'default' },
];

const STATUS_MAP: Record<string, { status: 'success' | 'error' | 'default' | 'processing'; text: string }> = {
  active: { status: 'success', text: '正常' },
  inactive: { status: 'default', text: '未启用' },
  error: { status: 'error', text: '异常' },
};

export const ModelProviderManager: React.FC = () => {
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [selectedType, setSelectedType] = useState<string>('bedrock');
  const [editSelectedType, setEditSelectedType] = useState<string>('bedrock');
  const [testingId, setTestingId] = useState<string | null>(null);

  const {
    providers,
    loading,
    createModalVisible,
    editModalVisible,
    deleteModalVisible,
    selectedProvider,
    fetchProviders,
    setCreateModalVisible,
    setEditModalVisible,
    setDeleteModalVisible,
    createProvider,
    updateProvider,
    deleteProvider,
    testConnection,
    handleEditProvider,
    handleDeleteProvider,
  } = useModelStore();

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  useEffect(() => {
    if (createModalVisible) {
      createForm.resetFields();
      setSelectedType('bedrock');
    }
  }, [createModalVisible, createForm]);

  useEffect(() => {
    if (selectedProvider && editModalVisible) {
      editForm.setFieldsValue({
        name: selectedProvider.name,
        type: selectedProvider.type,
        models: selectedProvider.models,
        is_default: selectedProvider.is_default,
        ...selectedProvider.config,
      });
      setEditSelectedType(selectedProvider.type);
    }
  }, [selectedProvider, editModalVisible, editForm]);

  const handleCreate = async (values: any) => {
    const { name, type, models, is_default, ...configFields } = values;
    await createProvider({
      name,
      type,
      config: configFields,
      models: models || [],
      is_default: is_default || false,
    });
    createForm.resetFields();
  };

  const handleUpdate = async (values: any) => {
    if (!selectedProvider) return;
    const { name, type, models, is_default, ...configFields } = values;
    await updateProvider(selectedProvider.id, {
      name,
      type,
      config: configFields,
      models: models || [],
      is_default: is_default || false,
    });
    editForm.resetFields();
  };

  const handleTestConnection = async (record: ModelProviderType) => {
    setTestingId(record.id);
    try {
      await testConnection(record.id);
    } finally {
      setTestingId(null);
    }
  };

  const getProviderColor = (type: string): string => {
    return PROVIDER_TYPES.find((p) => p.value === type)?.color || 'default';
  };

  const getProviderLabel = (type: string): string => {
    return PROVIDER_TYPES.find((p) => p.value === type)?.label || type;
  };

  // Render config fields based on provider type
  const renderConfigFields = (providerType: string) => {
    switch (providerType) {
      case 'bedrock':
        return (
          <Form.Item
            name="region"
            label="Region"
            rules={[{ required: true, message: '请输入 AWS Region' }]}
            initialValue="us-east-1"
          >
            <Input placeholder="例如: us-east-1" />
          </Form.Item>
        );
      case 'openai':
        return (
          <>
            <Form.Item
              name="base_url"
              label="Base URL"
              rules={[{ required: true, message: '请输入 Base URL' }]}
              initialValue="https://api.openai.com/v1"
            >
              <Input placeholder="https://api.openai.com/v1" />
            </Form.Item>
            <Form.Item
              name="api_key"
              label="API Key"
              rules={[{ required: true, message: '请输入 API Key' }]}
            >
              <Input.Password placeholder="sk-..." />
            </Form.Item>
          </>
        );
      case 'ollama':
        return (
          <Form.Item
            name="base_url"
            label="Base URL"
            rules={[{ required: true, message: '请输入 Ollama Base URL' }]}
            initialValue="http://localhost:11434"
          >
            <Input placeholder="http://localhost:11434" />
          </Form.Item>
        );
      case 'litellm':
        return (
          <>
            <Form.Item
              name="base_url"
              label="Base URL"
              rules={[{ required: true, message: '请输入 LiteLLM Base URL' }]}
            >
              <Input placeholder="http://localhost:4000" />
            </Form.Item>
            <Form.Item name="api_key" label="API Key">
              <Input.Password placeholder="可选" />
            </Form.Item>
          </>
        );
      case 'custom':
        return (
          <>
            <Form.Item
              name="base_url"
              label="Base URL"
              rules={[{ required: true, message: '请输入 Base URL' }]}
            >
              <Input placeholder="http://..." />
            </Form.Item>
            <Form.Item name="api_key" label="API Key">
              <Input.Password placeholder="可选" />
            </Form.Item>
          </>
        );
      default:
        return null;
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => (
        <Tag color={getProviderColor(type)}>{getProviderLabel(type)}</Tag>
      ),
    },
    {
      title: '可用模型数',
      dataIndex: 'models',
      key: 'models',
      width: 120,
      render: (models: string[]) => (
        <Tooltip title={models?.length ? models.join(', ') : '暂无模型'}>
          <span style={{ cursor: 'pointer' }}>{models?.length || 0}</span>
        </Tooltip>
      ),
    },
    {
      title: '默认',
      dataIndex: 'is_default',
      key: 'is_default',
      width: 80,
      render: (isDefault: boolean) =>
        isDefault ? <Tag color="blue">默认</Tag> : null,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = STATUS_MAP[status] || { status: 'default' as const, text: status || '未知' };
        return <Badge status={config.status} text={config.text} />;
      },
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right' as const,
      width: 200,
      render: (_: unknown, record: ModelProviderType) => (
        <Space>
          <Tooltip title="测试连接">
            <Button
              type="text"
              icon={testingId === record.id ? <LoadingOutlined /> : <ApiOutlined />}
              onClick={() => handleTestConnection(record)}
              disabled={testingId === record.id}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditProvider(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteProvider(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const formContent = (providerType: string, onTypeChange: (val: string) => void) => (
    <>
      <Form.Item
        name="name"
        label="名称"
        rules={[
          { required: true, message: '请输入 Provider 名称' },
          { max: 100, message: '名称不能超过100个字符' },
        ]}
      >
        <Input placeholder="例如: My OpenAI Provider" />
      </Form.Item>

      <Form.Item
        name="type"
        label="类型"
        rules={[{ required: true, message: '请选择 Provider 类型' }]}
      >
        <Select
          placeholder="选择 Provider 类型"
          onChange={(val: string) => onTypeChange(val)}
          options={PROVIDER_TYPES.map((p) => ({
            value: p.value,
            label: p.label,
          }))}
        />
      </Form.Item>

      {renderConfigFields(providerType)}

      <Form.Item name="models" label="可用模型">
        <Select
          mode="tags"
          placeholder="输入模型名称并回车添加"
          tokenSeparators={[',']}
        />
      </Form.Item>

      <Form.Item name="is_default" label="设为默认" valuePropName="checked">
        <Switch />
      </Form.Item>
    </>
  );

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <Title level={2}>模型管理</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新增 Provider
          </Button>
        </div>

        <Paragraph>
          管理 LLM 模型提供商配置，支持 Bedrock、OpenAI、Ollama、LiteLLM 等多种模型。
        </Paragraph>

        <Table
          columns={columns}
          dataSource={providers}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
          pagination={{
            defaultPageSize: 10,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'],
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />

        {/* Create Modal */}
        <Modal
          title="新增模型 Provider"
          open={createModalVisible}
          onCancel={() => setCreateModalVisible(false)}
          onOk={() => createForm.submit()}
          width={700}
          okText="创建"
          cancelText="取消"
          destroyOnClose
        >
          <Form
            form={createForm}
            layout="vertical"
            onFinish={handleCreate}
            initialValues={{ type: 'bedrock', is_default: false }}
          >
            {formContent(selectedType, setSelectedType)}
          </Form>
        </Modal>

        {/* Edit Modal */}
        <Modal
          title="编辑模型 Provider"
          open={editModalVisible}
          onCancel={() => setEditModalVisible(false)}
          onOk={() => editForm.submit()}
          width={700}
          okText="保存"
          cancelText="取消"
          destroyOnClose
        >
          <Form
            form={editForm}
            layout="vertical"
            onFinish={handleUpdate}
          >
            {formContent(editSelectedType, setEditSelectedType)}
          </Form>
        </Modal>

        {/* Delete Confirmation Modal */}
        <Modal
          title="确认删除"
          open={deleteModalVisible}
          onCancel={() => setDeleteModalVisible(false)}
          onOk={() => {
            if (selectedProvider) {
              deleteProvider(selectedProvider.id);
            }
          }}
          okText="确认"
          cancelText="取消"
          okButtonProps={{ danger: true }}
        >
          <p>
            确定要删除模型 Provider{' '}
            {selectedProvider ? `[${selectedProvider.name}]` : ''} 吗？
          </p>
          <p>删除后无法恢复，请谨慎操作。</p>
        </Modal>
      </Card>
    </div>
  );
};
