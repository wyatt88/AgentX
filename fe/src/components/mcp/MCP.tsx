import React, { useEffect } from 'react';
import { 
  Card, Typography, Table, Button, Space, Modal, 
  Form, Input, Select, Tooltip, Tag, Badge, Spin,
} from 'antd';
import { 
  PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined,
  HeartOutlined, SyncOutlined, ToolOutlined,
} from '@ant-design/icons';
import { useMCPStore } from '../../store';
import type { MCPServer } from '../../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const STATUS_CONFIG: Record<string, { status: 'success' | 'error' | 'default' | 'processing'; text: string }> = {
  running: { status: 'success', text: '运行中' },
  stopped: { status: 'default', text: '已停止' },
  error: { status: 'error', text: '异常' },
  unknown: { status: 'processing', text: '未知' },
};

export const MCP: React.FC = () => {
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  
  const { 
    mcpServers, groups, serverTools, loading, 
    healthCheckLoading, healthCheckAllLoading, toolsLoading,
    createModalVisible, editModalVisible, detailModalVisible, 
    deleteModalVisible, toolsModalVisible, selectedServer, selectedGroupFilter,
    fetchMCPServers, fetchGroups,
    setCreateModalVisible, setEditModalVisible, setDetailModalVisible,
    setDeleteModalVisible, setToolsModalVisible, setSelectedGroupFilter,
    createMCPServer, updateMCPServer, deleteMCPServer,
    handleViewServer, handleEditServer, handleDeleteServer,
    healthCheck, healthCheckAll, getServerTools,
  } = useMCPStore();
  
  useEffect(() => {
    if (createModalVisible) createForm.resetFields();
  }, [createModalVisible, createForm]);
  
  useEffect(() => {
    if (selectedServer && editModalVisible) {
      editForm.setFieldsValue({ ...selectedServer, tags: selectedServer.tags || [] });
    }
  }, [selectedServer, editModalVisible, editForm]);
  
  useEffect(() => {
    fetchMCPServers();
    fetchGroups();
  }, [fetchMCPServers, fetchGroups]);
  
  const handleCreateMCPServer = async (values: Omit<MCPServer, 'id'>) => {
    await createMCPServer(values);
    createForm.resetFields();
  };
  
  const handleUpdateMCPServer = async (values: MCPServer) => {
    await updateMCPServer(values);
    editForm.resetFields();
  };

  const filteredServers = selectedGroupFilter
    ? mcpServers.filter(s => s.group === selectedGroupFilter)
    : mcpServers;

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 150 },
    {
      title: '分组', dataIndex: 'group', key: 'group', width: 100,
      render: (group: string) => group ? <Tag>{group}</Tag> : <Tag color="default">未分组</Tag>,
    },
    { title: '描述', dataIndex: 'desc', key: 'desc', width: 200, ellipsis: true },
    {
      title: '主机地址', dataIndex: 'host', key: 'host', width: 220, ellipsis: true,
      render: (host: string) => <Tooltip title={host}><span>{host}</span></Tooltip>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (status: string) => {
        const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.unknown;
        return <Badge status={cfg.status} text={cfg.text} />;
      },
    },
    {
      title: '工具数', dataIndex: 'tool_count', key: 'tool_count', width: 80,
      render: (count: number, record: MCPServer) => (
        <Button type="link" size="small" onClick={() => getServerTools(record)}>
          {count ?? '-'}
        </Button>
      ),
    },
    {
      title: '操作', key: 'actions', fixed: 'right' as const, width: 180,
      render: (_: unknown, record: MCPServer) => (
        <Space>
          <Tooltip title="查看"><Button type="text" icon={<EyeOutlined />} onClick={() => handleViewServer(record)} /></Tooltip>
          <Tooltip title="健康检查"><Button type="text" icon={<HeartOutlined />} loading={healthCheckLoading} onClick={() => healthCheck(record.id)} /></Tooltip>
          <Tooltip title="编辑"><Button type="text" icon={<EditOutlined />} onClick={() => handleEditServer(record)} /></Tooltip>
          <Tooltip title="删除"><Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDeleteServer(record)} /></Tooltip>
        </Space>
      ),
    },
  ];

  const serverFormFields = (
    <>
      <Form.Item name="name" label="MCP服务器名称"
        rules={[{ required: true, message: '请输入MCP服务器名称' }, { max: 100, message: '名称不能超过100个字符' }]}>
        <Input placeholder="例如: MySQL Server" />
      </Form.Item>
      <Form.Item name="desc" label="描述" rules={[{ required: true, message: '请输入描述' }]}>
        <TextArea rows={3} placeholder="描述MCP服务器的功能和能力" />
      </Form.Item>
      <Form.Item name="host" label="主机地址" rules={[{ required: true, message: '请输入主机地址' }]}>
        <Input placeholder="例如: http://localhost:8001" />
      </Form.Item>
      <Form.Item name="group" label="分组">
        <Select allowClear placeholder="选择或输入分组"
          options={groups.map(g => ({ value: g, label: g }))} showSearch />
      </Form.Item>
      <Form.Item name="tags" label="标签">
        <Select mode="tags" placeholder="输入标签后回车" tokenSeparators={[',']} />
      </Form.Item>
    </>
  );

  const serverDetailContent = selectedServer && (
    <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: '10px' }}>基本信息</h3>
        <p><strong>ID:</strong> {selectedServer.id}</p>
        <p><strong>名称:</strong> {selectedServer.name}</p>
        <p><strong>描述:</strong> {selectedServer.desc}</p>
        <p><strong>主机地址:</strong> {selectedServer.host}</p>
        <p><strong>分组:</strong> {selectedServer.group || '未分组'}</p>
        <p><strong>标签:</strong>{' '}
          {selectedServer.tags?.length ? selectedServer.tags.map(tag => <Tag key={tag}>{tag}</Tag>) : '无'}
        </p>
        <p><strong>状态:</strong>{' '}
          {(() => { const cfg = STATUS_CONFIG[selectedServer.status || 'unknown'] || STATUS_CONFIG.unknown; return <Badge status={cfg.status} text={cfg.text} />; })()}
        </p>
        <p><strong>工具数:</strong> {selectedServer.tool_count ?? '未知'}</p>
      </div>
    </div>
  );

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Title level={2}>MCP Hub</Title>
          <Space>
            <Button icon={<SyncOutlined spin={healthCheckAllLoading} />}
              loading={healthCheckAllLoading} onClick={() => healthCheckAll()}>
              全部检查
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              新增
            </Button>
          </Space>
        </div>
        <Paragraph>管理和监控您的 Model Context Protocol (MCP) 服务器。支持分组筛选、健康检查和工具列表查看。</Paragraph>
        <div style={{ marginBottom: '16px' }}>
          <Space>
            <span>分组筛选:</span>
            <Select allowClear placeholder="全部分组" style={{ width: 200 }}
              value={selectedGroupFilter} onChange={(val) => setSelectedGroupFilter(val)}
              options={groups.map(g => ({ value: g, label: g }))} />
          </Space>
        </div>
        <Table columns={columns} dataSource={filteredServers} rowKey="id" loading={loading}
          scroll={{ x: 1100 }} pagination={{ defaultPageSize: 10, showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'], showTotal: (total) => `共 ${total} 条记录` }} />

        {/* Create Modal */}
        <Modal title="新增 MCP 服务器" open={createModalVisible}
          onCancel={() => setCreateModalVisible(false)} onOk={() => createForm.submit()}
          width={700} okText="创建" cancelText="取消" destroyOnClose>
          <Form form={createForm} layout="vertical" onFinish={handleCreateMCPServer}
            initialValues={{ name: '', desc: '', host: '', group: undefined, tags: [] }}>
            {serverFormFields}
          </Form>
        </Modal>

        {/* Edit Modal */}
        <Modal title="编辑 MCP 服务器" open={editModalVisible}
          onCancel={() => setEditModalVisible(false)} onOk={() => editForm.submit()}
          width={700} okText="保存" cancelText="取消" destroyOnClose>
          <Form form={editForm} layout="vertical" onFinish={handleUpdateMCPServer}>
            <Form.Item name="id" hidden><Input /></Form.Item>
            {serverFormFields}
          </Form>
        </Modal>

        {/* Detail Modal */}
        <Modal title="MCP 服务器详情" open={detailModalVisible}
          onCancel={() => setDetailModalVisible(false)} width={700}
          footer={[<Button key="close" onClick={() => setDetailModalVisible(false)}>关闭</Button>]}>
          {serverDetailContent}
        </Modal>

        {/* Delete Modal */}
        <Modal title="确认删除" open={deleteModalVisible}
          onCancel={() => setDeleteModalVisible(false)}
          onOk={() => deleteMCPServer(selectedServer?.id || '')}
          okText="确认" cancelText="取消" okButtonProps={{ danger: true }}>
          <p>确定要删除 {selectedServer ? "[" + selectedServer.name + "]" : "MCP"} 服务器吗？</p>
          <p>删除后无法恢复，请谨慎操作。</p>
        </Modal>

        {/* Tools Modal */}
        <Modal title={`工具列表 - ${selectedServer?.name || ''}`} open={toolsModalVisible}
          onCancel={() => setToolsModalVisible(false)} width={800}
          footer={[<Button key="close" onClick={() => setToolsModalVisible(false)}>关闭</Button>]}>
          {toolsLoading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}><Spin tip="加载工具列表中..." /></div>
          ) : (
            <Table dataSource={serverTools} rowKey="name" pagination={false} size="small"
              columns={[
                { title: '工具名称', dataIndex: 'name', key: 'name', width: 200,
                  render: (name: string) => <Space><ToolOutlined /><span style={{ fontFamily: 'monospace' }}>{name}</span></Space> },
                { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
              ]}
              locale={{ emptyText: '该服务器暂无可用工具' }} />
          )}
        </Modal>
      </Card>
    </div>
  );
};
