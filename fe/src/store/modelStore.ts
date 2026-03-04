import { create } from 'zustand';
import { message } from 'antd';
import { modelAPI } from '../services/api';
import type {
  ModelProvider,
  CreateModelProviderReq,
  UpdateModelProviderReq,
} from '../types';

interface ModelProviderState {
  // Data
  providers: ModelProvider[];

  // UI State
  loading: boolean;
  createModalVisible: boolean;
  editModalVisible: boolean;
  deleteModalVisible: boolean;
  selectedProvider: ModelProvider | null;

  // Actions
  fetchProviders: () => Promise<void>;
  setCreateModalVisible: (visible: boolean) => void;
  setEditModalVisible: (visible: boolean) => void;
  setDeleteModalVisible: (visible: boolean) => void;
  setSelectedProvider: (provider: ModelProvider | null) => void;
  createProvider: (data: CreateModelProviderReq) => Promise<void>;
  updateProvider: (id: string, data: UpdateModelProviderReq) => Promise<void>;
  deleteProvider: (id: string) => Promise<void>;
  testConnection: (id: string) => Promise<{ success: boolean; message: string }>;
  handleEditProvider: (provider: ModelProvider) => void;
  handleDeleteProvider: (provider: ModelProvider) => void;
}

export const useModelStore = create<ModelProviderState>((set, get) => ({
  // Initial state
  providers: [],
  loading: false,
  createModalVisible: false,
  editModalVisible: false,
  deleteModalVisible: false,
  selectedProvider: null,

  // Actions
  fetchProviders: async () => {
    set({ loading: true });
    try {
      const data = await modelAPI.getProviders();
      set({ providers: data as ModelProvider[] });
    } catch (error) {
      message.error('获取模型 Provider 列表失败');
      console.error('Error fetching model providers:', error);
    } finally {
      set({ loading: false });
    }
  },

  setCreateModalVisible: (visible) => set({ createModalVisible: visible }),
  setEditModalVisible: (visible) => set({ editModalVisible: visible }),
  setDeleteModalVisible: (visible) => set({ deleteModalVisible: visible }),
  setSelectedProvider: (provider) => set({ selectedProvider: provider }),

  createProvider: async (data) => {
    try {
      await modelAPI.createProvider(data);
      message.success('模型 Provider 创建成功');
      set({ createModalVisible: false });
      get().fetchProviders();
    } catch (error) {
      message.error('创建模型 Provider 失败');
      console.error('Error creating model provider:', error);
    }
  },

  updateProvider: async (id, data) => {
    try {
      await modelAPI.updateProvider(id, data);
      message.success('模型 Provider 更新成功');
      set({ editModalVisible: false });
      get().fetchProviders();
    } catch (error) {
      message.error('更新模型 Provider 失败');
      console.error('Error updating model provider:', error);
    }
  },

  deleteProvider: async (id) => {
    try {
      await modelAPI.deleteProvider(id);
      message.success('模型 Provider 删除成功');
      set({ deleteModalVisible: false, selectedProvider: null });
      get().fetchProviders();
    } catch (error) {
      message.error('删除模型 Provider 失败');
      console.error('Error deleting model provider:', error);
    }
  },

  testConnection: async (id) => {
    try {
      const result = await modelAPI.testConnection(id);
      if (result.success) {
        message.success('连接测试成功');
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
      return result;
    } catch (error) {
      const result = { success: false, message: '连接测试异常' };
      message.error(result.message);
      return result;
    }
  },

  handleEditProvider: (provider) => {
    set({
      selectedProvider: provider,
      editModalVisible: true,
    });
  },

  handleDeleteProvider: (provider) => {
    set({
      selectedProvider: provider,
      deleteModalVisible: true,
    });
  },
}));
