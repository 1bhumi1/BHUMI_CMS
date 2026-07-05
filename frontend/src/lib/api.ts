import axios from 'axios';
import { getAccessToken, getRefreshToken, setTokens, removeTokens } from './auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach access token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 Unauthorized and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();
      
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          if (res.data?.data) {
            setTokens(res.data.data.access_token, res.data.data.refresh_token);
            originalRequest.headers.Authorization = `Bearer ${res.data.data.access_token}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          // If refresh fails, log out
          removeTokens();
          window.location.href = '/login';
        }
      } else {
        removeTokens();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);
