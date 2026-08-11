/**
 * Authentication Service
 * Handles all authentication-related API calls.
 */

import apiClient from './api';

const AUTH_BASE = '/auth';

export const authService = {
  /**
   * Register a new user
   */
  async register(email, password, displayName = null) {
    const response = await apiClient.post(`${AUTH_BASE}/register`, {
      email,
      password,
      display_name: displayName,
    });
    return response.data;
  },

  /**
   * Login user
   */
  async login(email, password) {
    const response = await apiClient.post(`${AUTH_BASE}/login`, {
      email,
      password,
    });
    return response.data;
  },

  /**
   * Logout user
   */
  async logout() {
    const response = await apiClient.post(`${AUTH_BASE}/logout`);
    return response.data;
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken = null) {
    const response = await apiClient.post(
      `${AUTH_BASE}/refresh`,
      refreshToken ? { refresh_token: refreshToken } : null,
      {
        withCredentials: true, // Allow cookies
      }
    );
    return response.data;
  },

  /**
   * Get current user info
   */
  async getCurrentUser(accessToken) {
    const response = await apiClient.get(`${AUTH_BASE}/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    return response.data;
  },
};

export default authService;
