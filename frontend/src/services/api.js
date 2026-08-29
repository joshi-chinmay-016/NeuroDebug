/**
 * API Client Service
 * Centralized API communication layer with JWT Bearer Token injection
 * and automatic refresh token rotation for NeuroDebug frontend.
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const ACCESS_TOKEN_KEY = 'neurodebug_access_token';
const REFRESH_TOKEN_KEY = 'neurodebug_refresh_token';
const USER_DATA_KEY = 'neurodebug_user_data';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add Request ID and JWT Authorization Bearer Token
apiClient.interceptors.request.use(
  (config) => {
    const requestId = Math.random().toString(36).substring(2, 10);
    config.headers['X-Request-ID'] = requestId;

    // Attach JWT Access Token if available
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling and automatic token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized by attempting to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const newAccessToken = res.data.access_token;
          const newRefreshToken = res.data.refresh_token || refreshToken;

          localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken);
          localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);

          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        } catch {
          console.warn('Refresh token expired or invalid, clearing auth session');
          localStorage.removeItem(ACCESS_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          localStorage.removeItem(USER_DATA_KEY);
        }
      }
    }

    const errorMessage =
      error.response?.data?.detail?.message ||
      error.response?.data?.detail ||
      error.message ||
      'API request failed';
    return Promise.reject(new Error(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage)));
  }
);

export default apiClient;
