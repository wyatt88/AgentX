import { create } from 'zustand';
import { message } from 'antd';
import { mcpAPI } from '../services/api';
import type { MCPServer } from '../services/api';

interface MCPState {
  // Data
  mcpServers: MCPServer[];
  groups: string[];
  serverTools: Array<{ name: string; description: string; input_schema?: Record<string, any> }>;
  
  // UI State
  loading: boolean;
  healthCheckLoading: boolean;
  healthCheckAllLoading: boolean;
  toolsLoading: boolean;
  createModalVisible: boolean;
  editModalVisible: boolean;
  detailModalVisible: boolean;
  deleteModalVisible: boolean;
  toolsModalVisible: boolean;
  selectedServer: MCPServer | null;
  selectedGroupFilter: string | undefined;
  
  // Actions
  fetchMCPServers: () => Promise<void>;
  fetchGroups: () => Promise<void>;
  setCreateModalVisible: (visible: boolean) => void;
  setEditModalVisible: (visible: boolean) => void;
  setDetailModalVisible: (visible: boolean) => void;
  setDeleteModalVisible: (visible: boolean) => void;
  setToolsModalVisible: (visible: boolean) => void;
  setSelectedServer: (server: MCPServer | null) => void;
  setSelectedGroupFilter: (group: string | undefined) => void;
  createMCPServer: (server: Omit<MCPServer, 'id'>) => Promise<void>;
  updateMCPServer: (server: MCPServer) => Promise<void>;
  deleteMCPServer: (id: string) => void;
  handleViewServer: (server: MCPServer) => void;
  handleEditServer: (server: MCPServer) => void;
  handleDeleteServer: (server: MCPServer) => void;
  healthCheck: (id: string) => Promise<void>;
  healthCheckAll: () => Promise<void>;
  getServerTools: (server: MCPServer) => Promise<void>;
}

export const useMCPStore = create<MCPState>((set, get) => ({
  // Initial state
  mcpServers: [],
  groups: [],
  serverTools: [],
  loading: false,
  healthCheckLoading: false,
  healthCheckAllLoading: false,
  toolsLoading: false,
  createModalVisible: false,
  editModalVisible: false,
  detailModalVisible: false,
  deleteModalVisible: false,
  toolsModalVisible: false,
  selectedServer: null,
  selectedGroupFilter: undefined,
  
  // Actions
  fetchMCPServers: async () => {
    set({ loading: true });
    try {
      const data = await mcpAPI.getMCPServers();
      set({ mcpServers: data });
    } catch (error) {
      message.error('获取MCP服务器列表失败');
      console.error('Error fetching MCP servers:', error);
    } finally {
      set({ loading: false });
    }
  },

  fetchGroups: async () => {
    try {
      const data = await mcpAPI.getGroups();
      set({ groups: data });
    } catch (error) {
      console.error('Error fetching MCP groups:', error);
    }
  },
  
  setCreateModalVisible: (visible) => set({ createModalVisible: visible }),
  
  setEditModalVisible: (visible) => set({ editModalVisible: visible }),
  
  setDetailModalVisible: (visible) => set({ detailModalVisible: visible }),

  setDeleteModalVisible: (visible) => set({ deleteModalVisible: visible }),

  setToolsModalVisible: (visible) => set({ toolsModalVisible: visible }),
  
  setSelectedServer: (server) => set({ selectedServer: server }),

  setSelectedGroupFilter: (group) => set({ selectedGroupFilter: group }),
  
  createMCPServer: async (server) => {
    try {
      await mcpAPI.createOrUpdateMCPServer(server);
      message.success('MCP服务器创建成功');
      set({ createModalVisible: false });
      get().fetchMCPServers(); // Refresh the list
    } catch (error) {
      message.error('创建MCP服务器失败');
      console.error('Error creating MCP server:', error);
    }
  },
  
  updateMCPServer: async (server) => {
    try {
      await mcpAPI.createOrUpdateMCPServer(server);
      message.success('MCP服务器更新成功');
      set({ editModalVisible: false });
      get().fetchMCPServers(); // Refresh the list
    } catch (error) {
      message.error('更新MCP服务器失败');
      console.error('Error updating MCP server:', error);
    }
  },
  
  deleteMCPServer: (id) => {
    try {
      // First update the UI immediately for better user experience
      const { mcpServers } = get();
      set({ mcpServers: mcpServers.filter(server => server.id !== id) });
      
      // Then call the API in the background
      mcpAPI.deleteMCPServer(id)
        .then(() => {
          message.success('MCP服务器删除成功');
          set({ deleteModalVisible: false });
          get().fetchMCPServers(); // Refresh the list
        })
        .catch((error) => {
          message.error('删除MCP服务器失败');
          console.error('Error deleting MCP server:', error);
          // Refresh the list to restore the server if API call failed
          get().fetchMCPServers();
        });
    } catch (error) {
      message.error('删除MCP服务器失败');
      console.error('Error deleting MCP server:', error);
    }
  },
  
  handleViewServer: (server) => {
    set({ 
      selectedServer: server,
      detailModalVisible: true
    });
  },
  
  handleEditServer: (server) => {
    set({ 
      selectedServer: server,
      editModalVisible: true
    });
  },
  handleDeleteServer: (server) => {
    set({ 
      selectedServer: server,
      deleteModalVisible: true
    });
  },

  healthCheck: async (id) => {
    set({ healthCheckLoading: true });
    try {
      const result = await mcpAPI.healthCheck(id);
      // Update the server status in the local list
      const { mcpServers } = get();
      set({
        mcpServers: mcpServers.map(server =>
          server.id === id ? { ...server, status: result.status as MCPServer['status'] } : server
        ),
      });
      if (result.status === 'running') {
        message.success('健康检查通过');
      } else {
        message.warning(`健康检查: ${result.message || result.status}`);
      }
    } catch (error) {
      message.error('健康检查失败');
      console.error('Error health checking MCP server:', error);
    } finally {
      set({ healthCheckLoading: false });
    }
  },

  healthCheckAll: async () => {
    set({ healthCheckAllLoading: true });
    try {
      const results = await mcpAPI.healthCheckAll();
      // Update all server statuses
      const { mcpServers } = get();
      const statusMap = new Map(results.map(r => [r.server_id, r.status]));
      set({
        mcpServers: mcpServers.map(server => {
          const newStatus = statusMap.get(server.id);
          return newStatus ? { ...server, status: newStatus as MCPServer['status'] } : server;
        }),
      });
      message.success('全部健康检查完成');
    } catch (error) {
      message.error('全部健康检查失败');
      console.error('Error health checking all MCP servers:', error);
    } finally {
      set({ healthCheckAllLoading: false });
    }
  },

  getServerTools: async (server) => {
    set({ toolsLoading: true, selectedServer: server, toolsModalVisible: true, serverTools: [] });
    try {
      const tools = await mcpAPI.getServerTools(server.id);
      set({ serverTools: tools });
    } catch (error) {
      message.error('获取工具列表失败');
      console.error('Error fetching server tools:', error);
    } finally {
      set({ toolsLoading: false });
    }
  },
}));
