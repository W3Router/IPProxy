/**
 * 共享的 API 路由配置
 * =================
 * 
 * 此文件定义了所有API路由，作为前后端的单一真实来源
 * 前端和后端都应该使用这个文件来保持路由的一致性
 */

// API 版本
export const API_VERSION = 'v2';

// API 基础路径
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// API 前缀
export const API_PREFIX = {
  OPEN: '/api/open',
  AUTH: '/api/auth',
  USER: '/api/user',
  ADMIN: '/api/admin',
  PROXY: '/api/proxy'
};

// 调试信息
function logDebugInfo() {
  if (process.env.NODE_ENV === 'development') {
    console.log('API Configuration:', {
      version: API_VERSION,
      baseUrl: API_BASE_URL,
      prefix: API_PREFIX
    });
  }
}

// API 路由配置
export const API_ROUTES = {
  AUTH: {
    LOGIN: `${API_PREFIX.AUTH}/login`,
    LOGOUT: `${API_PREFIX.AUTH}/logout`,
    REFRESH: `${API_PREFIX.AUTH}/refresh`
  },
  USER: {
    LIST: `${API_PREFIX.USER}/list`,
    CREATE: `${API_PREFIX.USER}/create`,
    UPDATE: `${API_PREFIX.USER}/{id}`,
    DELETE: `${API_PREFIX.USER}/{id}`
  },
  AGENT: {
    LIST: `${API_PREFIX.OPEN}/app/agent/list`,
    CREATE: `${API_PREFIX.OPEN}/app/proxy/user/v2`,
    UPDATE: `${API_PREFIX.OPEN}/app/agent/{id}`,
    STATISTICS: `${API_PREFIX.OPEN}/app/agent/{id}/statistics`,
    ORDERS: `${API_PREFIX.OPEN}/app/agent-orders/v2`,
    USERS: `${API_PREFIX.OPEN}/app/agent/{id}/users`
  },
  ORDER: {
    LIST: `${API_PREFIX.PROXY}/orders`,
    CREATE: `${API_PREFIX.PROXY}/order/create`,
    DETAIL: `${API_PREFIX.PROXY}/order/{id}`
  },
  PROXY: {
    LIST: `${API_PREFIX.PROXY}/list`,
    CREATE: `${API_PREFIX.PROXY}/create`,
    UPDATE: `${API_PREFIX.PROXY}/{id}`,
    DELETE: `${API_PREFIX.PROXY}/{id}`
  },
  AREA: {
    LIST: `${API_PREFIX.OPEN}/app/area/v2`
  },
  SETTINGS: {
    PRICES: `${API_PREFIX.OPEN}/app/settings/prices`,
    RESOURCES: `${API_PREFIX.OPEN}/app/settings/resources`
  }
};

// 初始化时打印调试信息
logDebugInfo();

// 导出 Python 兼容的路由配置
export const PYTHON_ROUTES = {
  ...API_ROUTES,
  // 添加 Python 特定的路由配置
};

// 为了方便 Python 使用，导出一个常量字符串版本
export const ROUTES_PY = `
from typing import Dict, Any

API_VERSION = "${API_VERSION}"
API_BASE = "${API_BASE_URL}"

API_PREFIX = {
    "OPEN": "${API_PREFIX.OPEN}",
    "AUTH": "${API_PREFIX.AUTH}",
    "USER": "${API_PREFIX.USER}",
    "ADMIN": "${API_PREFIX.ADMIN}",
    "PROXY": "${API_PREFIX.PROXY}"
}

API_ROUTES = {
    "AUTH": {
        "LOGIN": f"{API_PREFIX['AUTH']}/login",
        "LOGOUT": f"{API_PREFIX['AUTH']}/logout",
        "REFRESH": f"{API_PREFIX['AUTH']}/refresh"
    },
    "USER": {
        "LIST": f"{API_PREFIX['USER']}/list",
        "CREATE": f"{API_PREFIX['USER']}/create",
        "UPDATE": f"{API_PREFIX['USER']}/{{id}}",
        "DELETE": f"{API_PREFIX['USER']}/{{id}}"
    },
    "AGENT": {
        "LIST": f"{API_PREFIX['OPEN']}/app/agent/list",
        "CREATE": f"{API_PREFIX['OPEN']}/app/proxy/user/v2",
        "UPDATE": f"{API_PREFIX['OPEN']}/app/agent/{{id}}",
        "STATISTICS": f"{API_PREFIX['OPEN']}/app/agent/{{id}}/statistics",
        "ORDERS": f"{API_PREFIX['OPEN']}/app/agent-orders/v2",
        "USERS": f"{API_PREFIX['OPEN']}/app/agent/{{id}}/users"
    },
    "ORDER": {
        "LIST": f"{API_PREFIX['PROXY']}/orders",
        "CREATE": f"{API_PREFIX['PROXY']}/order/create",
        "DETAIL": f"{API_PREFIX['PROXY']}/order/{{id}}"
    },
    "PROXY": {
        "LIST": f"{API_PREFIX['PROXY']}/list",
        "CREATE": f"{API_PREFIX['PROXY']}/create",
        "UPDATE": f"{API_PREFIX['PROXY']}/{{id}}",
        "DELETE": f"{API_PREFIX['PROXY']}/{{id}}"
    },
    "AREA": {
        "LIST": f"{API_PREFIX['OPEN']}/app/area/v2"
    },
    "SETTINGS": {
        "PRICES": f"{API_PREFIX['OPEN']}/app/settings/prices",
        "RESOURCES": f"{API_PREFIX['OPEN']}/app/settings/resources"
    }
}
`; 