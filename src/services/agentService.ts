import type { AgentInfo, AgentStatistics, CreateAgentForm, UpdateAgentForm } from '@/types/agent';
import axios from 'axios';
import { debug } from '@/utils/debug';
import { API_ROUTES, API_PREFIX } from '@/shared/routes';
import request from '@/utils/request';

const { dashboard: debugAgent } = debug;

// 创建代理商服务专用的 axios 实例
const agentApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 添加请求拦截器，用于调试
agentApi.interceptors.request.use((config) => {
  // 添加token
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // 调试日志
  debugAgent.info('Request:', {
    url: config.url,
    baseURL: config.baseURL,
    method: config.method,
    params: config.params,
    data: config.data
  });
  
  return config;
});

interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

interface AgentOrder {
  id: string;
  order_no: string;
  amount: number;
  status: string;
  type: 'dynamic' | 'static';
  remark?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentListParams {
  page?: number;
  pageSize?: number;
  status?: string;
}

export interface AgentListResponse {
  total: number;
  list: AgentInfo[];
}

export async function getAgentList(params: AgentListParams): Promise<ApiResponse<AgentListResponse>> {
  try {
    console.log('获取代理商列表, 参数:', params);
    const response = await request.get('/api/open/app/agent/list', { 
      params: {
        page: params.page || 1,
        pageSize: params.pageSize || 100,  // 默认获取100条记录
        status: params.status || 'active'   // 默认只获取激活状态的代理商
      }
    });
    console.log('代理商列表响应:', response);
    
    // 直接返回响应数据，因为response已经被request拦截器处理过
    return response.data;
  } catch (error) {
    console.error('获取代理商列表失败:', error);
    throw error;
  }
}

export async function getAgentById(agentId: number): Promise<AgentInfo> {
  debugAgent.info('Getting agent by id:', agentId);
  const response = await agentApi.get<ApiResponse<AgentInfo>>(
    API_ROUTES.AGENT.UPDATE.replace('{id}', String(agentId))
  );
  debugAgent.info('Agent details response:', response.data);
  if (!response.data.data) {
    throw new Error('Agent not found');
  }
  return response.data.data;
}

export async function getAgentStatistics(agentId: number): Promise<AgentStatistics> {
  debugAgent.info('Getting agent statistics for id:', agentId);
  const response = await agentApi.get<ApiResponse<AgentStatistics>>(
    API_ROUTES.AGENT.STATISTICS.replace('{id}', String(agentId))
  );
  debugAgent.info('Agent statistics response:', response.data);
  return response.data.data;
}

export async function createAgent(params: CreateAgentForm): Promise<ApiResponse<AgentInfo>> {
  try {
    debugAgent.info('Creating agent with params:', {
      ...params,
      password: '******' // 隐藏密码
    });

    const requestData = {
      username: params.username,
      password: params.password,
      ...(params.email ? { email: params.email } : {}),
      ...(params.remark ? { remark: params.remark } : {}),
      ...(params.balance ? { balance: params.balance } : { balance: 1000.0 }),
      ...(params.phone ? { phone: params.phone } : {}),
      status: params.status ? (params.status === 'active' ? 1 : 0) : 1
    };
    
    debugAgent.info('Sending create agent request:', {
      ...requestData,
      password: '******'
    });

    const response = await agentApi.post<ApiResponse<AgentInfo>>(
      API_ROUTES.AGENT.CREATE,
      requestData
    );
    
    debugAgent.info('Create agent response:', response.data);

    if (!response.data) {
      throw new Error('API返回数据格式错误');
    }

    return response.data;
  } catch (error: any) {
    debugAgent.error('Failed to create agent:', error);
    if (error.response?.data) {
      debugAgent.error('API error response:', error.response.data);
      throw new Error(error.response.data.msg || '创建代理商失败');
    }
    throw error;
  }
}

export async function updateAgent(agentId: number, params: UpdateAgentForm): Promise<void> {
  debugAgent.info('Updating agent:', { agentId, params });
  const response = await agentApi.put<ApiResponse<void>>(
    API_ROUTES.AGENT.UPDATE.replace('{id}', String(agentId)),
    params
  );
  debugAgent.info('Update agent response:', response.data);
}

export async function getAgentOrders(params: {
  agentId: number;
  page: number;
  pageSize: number;
  status?: string;
  startDate?: string;
  endDate?: string;
}): Promise<ApiResponse<{ list: AgentOrder[]; total: number }>> {
  debugAgent.info('Getting agent orders:', params);
  const response = await agentApi.get<ApiResponse<{ list: AgentOrder[]; total: number }>>(
    API_ROUTES.AGENT.ORDERS,
    {
      params: {
        agentId: params.agentId,
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
        startDate: params.startDate,
        endDate: params.endDate
      }
    }
  );
  debugAgent.info('Agent orders response:', response.data);
  return response.data;
}

export async function getAgentUsers(params: {
  agentId: number;
  page: number;
  pageSize: number;
  status?: string;
}) {
  debugAgent.info('Getting agent users:', params);
  const response = await agentApi.get<ApiResponse<{ list: any[]; total: number }>>(
    API_ROUTES.AGENT.USERS.replace('{id}', String(params.agentId)),
    {
      params: {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status
      }
    }
  );
  debugAgent.info('Agent users response:', response.data);
  return response.data.data;
}

export async function updateAgentStatus(agentId: string, status: string): Promise<ApiResponse<AgentInfo>> {
  try {
    const response = await request.put<ApiResponse<AgentInfo>>(
      `${API_PREFIX.OPEN}/app/agent/${agentId}/status`,
      null,
      { params: { status } }
    );
    return response.data;
  } catch (error) {
    console.error('更新代理商状态失败:', error);
    throw error;
  }
}

export async function rechargeAgent(agentId: number, amount: number): Promise<ApiResponse<void>> {
  debugAgent.info('Recharging agent:', { agentId, amount });
  const response = await agentApi.post<ApiResponse<void>>(
    `/api/open/app/agent/${agentId}/recharge`,
    { amount }
  );
  debugAgent.info('Recharge response:', response.data);
  return response.data;
}

export async function adjustAgentQuota(agentId: number, quota: number): Promise<ApiResponse<void>> {
  debugAgent.info('Adjusting agent quota:', { agentId, quota });
  const response = await agentApi.post<ApiResponse<void>>(
    `/api/open/app/agent/${agentId}/quota`,
    { quota }
  );
  debugAgent.info('Adjust quota response:', response.data);
  return response.data;
}
