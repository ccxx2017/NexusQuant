import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1', // 从环境变量读取后端地址
  headers: {
    'Content-Type': 'application/json',
  },
});

// (可选) 添加请求拦截器，例如用于添加认证Token
// apiClient.interceptors.request.use(config => {
//   const token = localStorage.getItem('accessToken');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// (可选) 添加响应拦截器，例如用于统一处理错误
apiClient.interceptors.response.use(
  response => response,
  error => {
    // console.error('API Error:', error.response || error.message);
    // ElMessage.error(error.response?.data?.detail || error.message || '网络错误');
    return Promise.reject(error);
  }
);


// --- Dashboard APIs ---
// export const fetchDashboardSummary = () => apiClient.get('/dashboard/summary');

// --- Selection Strategy APIs ---
export const fetchSelectionStrategies = () => apiClient.get('/selection/strategies');
export const generateSelectionPool = (data) => apiClient.post('/selection/generate_pool', data);

// --- Timing Strategy APIs ---
export const fetchTimingStrategies = () => apiClient.get('/timing/strategies');
export const generateTimingSignals = (data) => apiClient.post('/timing/generate_signals', data); // 假设有此API

// --- Exit Strategy APIs ---
export const fetchExitStrategies = () => apiClient.get('/exit/strategies');
export const createHolding = (data) => apiClient.post('/exit/holdings', data);
export const fetchHoldings = (params) => apiClient.get('/exit/holdings', { params }); // params for pagination if needed
export const fetchHoldingById = (id) => apiClient.get(`/exit/holdings/${id}`);
export const updateHolding = (id, data) => apiClient.put(`/exit/holdings/${id}`, data);
export const deleteHolding = (id) => apiClient.delete(`/exit/holdings/${id}`);
export const checkExitSignalsForHoldings = (data) => apiClient.post('/exit/check_signals', data);

// --- Backtesting Lab APIs ---
export const runBacktest = (data) => apiClient.post('/backtesting_lab/run_backtest', data);
// export const getBacktestStatus = (taskId) => apiClient.get(`/backtesting_lab/status/${taskId}`);

export default apiClient;