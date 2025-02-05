/**
 * 用户服务模块
 * 
 * 此模块处理所有与用户相关的API请求，包括：
 * - 用户列表获取
 * - 用户状态管理
 * - 用户业务激活
 * 
 * 依赖说明：
 * - API基础配置：src/config/api.ts
 * - 类型定义：src/types/user.ts
 * - 工具函数：src/utils/request.ts
 * 
 * 后端对应：
 * - 路由：backend/app/routers/user.py
 * - 模型：backend/app/models/user.py
 */

import { api } from '@/utils/request';
import { API_PATHS } from '@/config/api';
import type { ApiResponse } from '@/types/api';
import type { User, UserListParams, UserListResponse, CreateUserParams } from '@/types/user';

export type { CreateUserParams };

/**
 * 获取用户列表
 * @param params 查询参数
 * 
 * 依赖说明：
 * - API路径: /api/user/list
 * - 后端函数: get_user_list (user.py)
 * 
 * 注意事项：
 * 1. 确保分页参数与后端一致
 * 2. 处理空数据的情况
 */
export async function getUserList(params: UserListParams): Promise<ApiResponse<UserListResponse>> {
  console.log('[User Service Debug] Calling getUserList with params:', params);
  const requestParams = {
    page: params.page,
    pageSize: params.pageSize,
    ...(params.username && { username: params.username }),
    ...(params.status && { status: params.status }),
    ...(params.dateRange?.[0] && { startTime: params.dateRange[0].format('YYYY-MM-DD HH:mm:ss') }),
    ...(params.dateRange?.[1] && { endTime: params.dateRange[1].format('YYYY-MM-DD HH:mm:ss') })
  };
  
  try {
    console.log('[User Service Debug] Sending request with params:', requestParams);
    const response = await api.get<ApiResponse<UserListResponse>>(API_PATHS.USER.MANAGE, {
      params: requestParams
    });
    
    console.log('[User Service Debug] Response data:', response);

    if (!response.data || !response.data.data) {
      throw new Error('Invalid response format');
    }

    const responseData = response.data.data;
    
    const userList = (responseData.list || []).map(user => {
      const userStatus = String(user.status).toLowerCase();
      return {
        ...user,
        status: userStatus === 'active' || userStatus === '1' ? 'active' as const : 'disabled' as const
      };
    });

    return {
      code: 0,
      msg: 'success',
      data: {
        list: userList,
        total: responseData.total || 0
      }
    };
    
  } catch (error) {
    console.error('[User Service Debug] API error:', error);
    return {
      code: -1,
      msg: error instanceof Error ? error.message : '获取用户列表失败',
      data: { list: [], total: 0 }
    };
  }
}

/**
 * 更新用户状态
 * @param userId 用户ID
 * @param status 新状态
 * 
 * 依赖说明：
 * - API路径: /api/user/{userId}/status
 * - 后端函数: update_user_status (user.py)
 * 
 * 注意事项：
 * 1. 确保状态值与后端枚举一致
 * 2. 状态更新后需要刷新用户列表
 */
export async function updateUserStatus(userId: string, status: string): Promise<ApiResponse<User>> {
  const response = await api.put<ApiResponse<User>>(API_PATHS.USER.UPDATE.replace('{id}', userId), { status });
  if (!response.data) {
    throw new Error('响应数据为空');
  }
  return response.data;
}

// 更新用户密码
export async function updateUserPassword(userId: string, password: string): Promise<ApiResponse<User>> {
  const response = await api.put<ApiResponse<User>>(`/open/app/user/${userId}/password`, { password });
  if (!response.data) {
    throw new Error('响应数据为空');
  }
  return response.data;
}

/**
 * 创建用户
 * @param params 用户创建参数
 * 
 * 依赖说明：
 * - API路径: /api/user/create
 * - 后端函数: create_user (user.py)
 * 
 * 注意事项：
 * 1. 确保必填字段完整
 * 2. 密码需要符合复杂度要求
 * 3. 创建成功后需要刷新用户列表
 */
export async function createUser(params: CreateUserParams): Promise<ApiResponse<User>> {
  const requestData = Object.fromEntries(
    Object.entries(params).filter(([_, value]) => value !== undefined && value !== '')
  );
  const response = await api.post<ApiResponse<User>>(API_PATHS.USER.CREATE, requestData);
  return response.data;
}

/**
 * 获取当前用户信息
 * 
 * 依赖说明：
 * - API路径: /api/user/profile
 * - 后端函数: get_user_profile (user.py)
 */
export async function getCurrentUser(): Promise<User> {
  const response = await api.get<ApiResponse<User>>(API_PATHS.USER.PROFILE);
  return response.data.data;
}

// 获取代理商列表
export async function getAgentList(): Promise<User[]> {
  const response = await api.get<ApiResponse<User[]>>('/api/agent/list');
  return response.data.data;
}

// 搜索用户
export async function searchUsers(params: any): Promise<ApiResponse<UserListResponse>> {
  const response = await api.get<ApiResponse<UserListResponse>>('/open/app/user/list', { params });
  return response.data;
}

// 格式化数字为千分位格式
export function formatNumber(num: number): string {
  return num.toLocaleString('zh-CN');
}

// 格式化流量大小
export function formatTraffic(gb: number): string {
  return `${gb}Gb`;
}

// 格式化数量
export function formatCount(count: number): string {
  return `${count}条`;
}

// 格式化百分比
export function formatPercent(percent: number): string {
  return `${percent}%`;
}
