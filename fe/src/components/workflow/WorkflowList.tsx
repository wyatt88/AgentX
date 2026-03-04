import React, { useEffect, useState } from 'react';
import {
  Card,
  Typography,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Tag,
  Empty,
  Spin,
  Tooltip,
  Popconfirm,
  message,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  ClockCircleOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { Workflow, WorkflowStatus } from './types';
import { workflowAPI } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// ----- Status helpers -----

const STATUS_CONFIG: Record<WorkflowStatus, { color: string; label: string }> = {
  draft: { color: 'default', label: '草稿' },
  published: { color: 'success', label: '已发布' },
  archived: { color: 'warning', label: '已归档' },
};

// ======================== Component ========================

export const WorkflowList: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [createForm] = Form.useForm();
  const navigate = useNavigate();

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const data = await workflowAPI.getWorkflows();
      setWorkflows(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleCreate = async (values: { name: string; description: string }) => {
    try {
      const wf = await workflowAPI.createWorkflow(values);
      if (wf) {
        message.success('工作流创建成功');
        setCreateModalVisible(false);
        createForm.resetFields();
        navigate(`/workflows/${wf.id}`);
      }
    } catch {
      message.error('创建失败');
    }
  };

  const handleDelete = async (id: string) => {
    const ok = await workflowAPI.deleteWorkflow(id);
    if (ok) {
      message.success('已删除');
      fetchWorkflows();
    } else {
      message.error('删除失败');
    }
  };

  const handleExecute = async (id: string) => {
    try {
      message.info('工作流开始执行');
      await workflowAPI.executeWorkflow(id, {});
    } catch {
      message.error('执行失败');
    }
  };

  const countNodes = (wf: Workflow): number => {
    return wf.definition?.nodes?.length ?? 0;
  };

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          <ApartmentOutlined style={{ marginRight: 8 }} />
          工作流管理
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          新建工作流
        </Button>
      </div>

      <Spin spinning={loading}>
        {workflows.length === 0 && !loading ? (
          <Empty description="暂无工作流，点击右上角新建" />
        ) : (
          <Row gutter={[16, 16]}>
            {workflows.map((wf) => {
              const statusCfg = STATUS_CONFIG[wf.status] || STATUS_CONFIG.draft;
              return (
                <Col key={wf.id} xs={24} sm={12} md={8} lg={6}>
                  <Card
                    hoverable
                    style={{ height: '100%' }}
                    actions={[
                      <Tooltip title="编辑" key="edit">
                        <EditOutlined onClick={() => navigate(`/workflows/${wf.id}`)} />
                      </Tooltip>,
                      <Tooltip title="执行" key="run">
                        <PlayCircleOutlined onClick={() => handleExecute(wf.id)} />
                      </Tooltip>,
                      <Popconfirm
                        key="del"
                        title="确认删除此工作流？"
                        onConfirm={() => handleDelete(wf.id)}
                        okText="确认"
                        cancelText="取消"
                      >
                        <Tooltip title="删除">
                          <DeleteOutlined style={{ color: '#ff4d4f' }} />
                        </Tooltip>
                      </Popconfirm>,
                    ]}
                  >
                    <Card.Meta
                      title={
                        <Space>
                          <span>{wf.name}</span>
                          <Tag color={statusCfg.color}>{statusCfg.label}</Tag>
                        </Space>
                      }
                      description={
                        <>
                          <Paragraph
                            type="secondary"
                            ellipsis={{ rows: 2 }}
                            style={{ marginBottom: 8 }}
                          >
                            {wf.description || '暂无描述'}
                          </Paragraph>
                          <Space size="middle">
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              <ApartmentOutlined /> {countNodes(wf)} 个节点
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              <ClockCircleOutlined />{' '}
                              {wf.updated_at
                                ? new Date(wf.updated_at).toLocaleDateString()
                                : '-'}
                            </Text>
                          </Space>
                        </>
                      }
                    />
                  </Card>
                </Col>
              );
            })}
          </Row>
        )}
      </Spin>

      {/* Create workflow modal */}
      <Modal
        title="新建工作流"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        onOk={() => createForm.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="工作流名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="例如：客户分类工作流" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="简要描述工作流用途" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
