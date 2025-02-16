import { Dayjs } from 'dayjs';
import moment from 'moment';

export enum UserRole {
  ADMIN = 'admin',
  AGENT = 'agent',
  USER = 'user'
}

export interface User {
  id: number;
  username: string;
  email?: string;
  agent_id?: number;  // 改为可选字段，不使用 null
  status: 'active' | 'disabled';
  balance: number;
  is_admin: boolean;
  is_agent: boolean;
  role: UserRole;  // 添加 role 字段
  remark?: string;
  created_at: string;
  updated_at: string;  // 改为必需字段，因为后端总是会返回这个字段
}

export interface UserProfile extends User {
  total_recharge: number;
  total_consumption: number;
}

export interface UserListParams {
  page: number;
  pageSize: number;
  username?: string;
  status?: string;
  dateRange?: [moment.Moment, moment.Moment];
}

export interface UserListResponse {
  list: User[];
  total: number;
}

export interface CreateUserParams {
  username: string;
  password: string;
  email?: string;
  remark?: string;
  agent_id?: number;  // 可选，代理商ID
}

export interface CreateUserForm extends CreateUserParams {
  confirmPassword?: string;  // 用于表单验证
}

export interface BusinessActivationForm {
  proxyType: 'dynamic' | 'static';
  dynamicPool?: string;
  trafficAmount?: number;
  region?: string;
  country?: string;
  city?: string;
  staticType?: string;
  ipRange?: string;
  duration?: number;
  quantity?: number;
  remark?: string;
}