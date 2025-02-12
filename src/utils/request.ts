import axios from 'axios';

// 自定义API错误类型
class ApiError extends Error {
  response?: any;
  constructor(message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

const request = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',  // 使用环境变量或默认为 /api
  timeout: 30000,  // 增加超时时间到 30 秒
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { data } = response;
    console.log('[API Response]', {
      url: response.config.url,
      method: response.config.method,
      status: response.status,
      data: data
    });
    
    // 统一处理成功响应
    // 1. 标准格式：code === 0
    // 2. HTTP成功：code === 200
    // 3. 无code但有data：兼容旧接口
    if (
      data.code === 0 || 
      data.code === 200 ||
      (data.data && !data.code)
    ) {
      // 统一转换为标准格式
      response.data = {
        code: 0,
        message: data.message || data.msg || '操作成功',
        data: data.data
      };
      return response;
    }
    
    // 处理错误响应
    const errorMessage = data.message || data.msg || '请求失败';
    const error = new ApiError(errorMessage);
    error.response = response;
    console.error('[API Error]', {
      url: response.config.url,
      method: response.config.method,
      status: response.status,
      error: data
    });
    throw error;
  },
  error => {
    if (error.response) {
      console.error('[API Error Response]', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response.status,
        data: error.response.data
      });
      
      // 处理401未授权错误
      if (error.response.status === 401) {
        localStorage.removeItem('token');  // 清除失效的token
        window.location.href = '/login';  // 重定向到登录页
        return Promise.reject(new Error('登录已过期，请重新登录'));
      }
      
      // 处理其他HTTP错误
      const errorMessage = error.response.data?.message || 
                          error.response.data?.msg || 
                          '请求失败';
      throw new Error(errorMessage);
    } else if (error.request) {
      console.error('[API Network Error]', {
        url: error.config?.url,
        method: error.config?.method,
        message: error.message
      });
      throw new Error('网络错误，请检查网络连接');
    } else {
      console.error('[API Error]', error.message);
      throw error;
    }
  }
);

// 为了保持兼容性，导出多个别名
export const api = request;
export const apiRequest = request;
export default request;