/**
 * Profile Service
 * Handles all profile-related API calls.
 */

import apiClient from './api';

const PROFILE_BASE = '/profile';

export const profileService = {
  /**
   * Get current user profile
   */
  async getProfile() {
    const response = await apiClient.get(`${PROFILE_BASE}/profile`);
    return response.data;
  },

  /**
   * Update user profile
   */
  async updateProfile(data) {
    const response = await apiClient.patch(`${PROFILE_BASE}/profile`, data);
    return response.data;
  },

  /**
   * Change password
   */
  async changePassword(data) {
    const response = await apiClient.post(`${PROFILE_BASE}/change-password`, data);
    return response.data;
  },
};

export default profileService;
