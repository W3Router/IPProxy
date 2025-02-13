export interface AgentInfo {
  id: string;
  app_username: string;
  platform_account: string;
  status: 'active' | 'disabled';
  balance: number;
  limit_flow: number;
  main_account: string;
  remark?: string;
  phone?: string;
  created_at: string;
  updated_at?: string;
}

export interface AgentStatistics {
  totalUsers: number;
  activeUsers: number;
  monthlyNewUsers: number;
  lastMonthNewUsers: number;
  totalOrders: number;
  activeOrders: number;
  totalIncome: number;
  monthlyIncome: number;
}

export interface CreateAgentForm {
  username: string;
  password: string;
  email?: string;
  balance?: number;
  phone?: string;
  remark?: string;
  status?: 'active' | 'disabled';
}

export interface UpdatePasswordForm {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface UpdateBalanceForm {
  amount: number;
  remark: string;
}

export interface UpdateAgentForm {
  status?: string;
  remark?: string;
  limit_flow?: number;
  balance?: number;
  app_username?: string;
  contact?: string;
}

export interface AgentOrder {
  id: number;
  orderNumber: string;
  userId: number;
  userAccount: string;
  amount: number;
  status: string;
  createdAt: string;
  type: 'dynamic' | 'static';
}

export interface AgentUser {
  id: number;
  account: string;
  email: string;
  status: 'active' | 'disabled';
  createdAt: string;
  lastLoginAt: string;
  totalOrders: number;
  totalSpent: number;
}

export interface Agent {
  id: number;
  username: string;
  email: string;
  balance: number;
  status: string;
  created_at: string;
  updated_at: string;
}