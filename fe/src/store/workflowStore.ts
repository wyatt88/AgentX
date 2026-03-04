import { create } from 'zustand';
import { message } from 'antd';
import { workflowAPI } from '../services/api';
import type {
  Workflow,
  CreateWorkflowReq,
  UpdateWorkflowReq,
} from '../types';

interface WorkflowState {
  // Data
  workflows: Workflow[];
  currentWorkflow: Workflow | null;

  // UI State
  loading: boolean;

  // Actions
  fetchWorkflows: () => Promise<void>;
  setCurrentWorkflow: (workflow: Workflow | null) => void;
  createWorkflow: (data: CreateWorkflowReq) => Promise<Workflow>;
  updateWorkflow: (id: string, data: UpdateWorkflowReq) => Promise<void>;
  deleteWorkflow: (id: string) => Promise<void>;
  executeWorkflow: (id: string, inputData: any) => Promise<Response>;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // Initial state
  workflows: [],
  currentWorkflow: null,
  loading: false,

  // Actions
  fetchWorkflows: async () => {
    set({ loading: true });
    try {
      const data = await workflowAPI.getWorkflows();
      set({ workflows: data as Workflow[] });
    } catch (error) {
      message.error('获取工作流列表失败');
      console.error('Error fetching workflows:', error);
    } finally {
      set({ loading: false });
    }
  },

  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),

  createWorkflow: async (data) => {
    try {
      const result = await workflowAPI.createWorkflow(data);
      message.success('工作流创建成功');
      get().fetchWorkflows();
      return result as Workflow;
    } catch (error) {
      message.error('创建工作流失败');
      console.error('Error creating workflow:', error);
      throw error;
    }
  },

  updateWorkflow: async (id, data) => {
    try {
      await workflowAPI.updateWorkflow(id, data);
      message.success('工作流更新成功');
      // If updating the current workflow, refresh it
      const { currentWorkflow } = get();
      if (currentWorkflow && currentWorkflow.id === id) {
        const updated = await workflowAPI.getWorkflow(id);
        if (updated) {
          set({ currentWorkflow: updated as Workflow });
        }
      }
      get().fetchWorkflows();
    } catch (error) {
      message.error('更新工作流失败');
      console.error('Error updating workflow:', error);
      throw error;
    }
  },

  deleteWorkflow: async (id) => {
    try {
      await workflowAPI.deleteWorkflow(id);
      message.success('工作流删除成功');
      // Clear current workflow if it was the deleted one
      const { currentWorkflow } = get();
      if (currentWorkflow && currentWorkflow.id === id) {
        set({ currentWorkflow: null });
      }
      get().fetchWorkflows();
    } catch (error) {
      message.error('删除工作流失败');
      console.error('Error deleting workflow:', error);
      throw error;
    }
  },

  executeWorkflow: async (id, inputData) => {
    try {
      const response = await workflowAPI.executeWorkflow(id, inputData);
      return response;
    } catch (error) {
      message.error('执行工作流失败');
      console.error('Error executing workflow:', error);
      throw error;
    }
  },
}));
