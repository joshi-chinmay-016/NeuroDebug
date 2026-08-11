/**
 * Analytics Service
 * Handles all analytics-related API calls.
 */

import apiClient from './api';

const ANALYTICS_BASE = '/analytics';

export const analyticsService = {
  /**
   * Get analytics data
   */
  async getAnalytics(days = 30) {
    const response = await apiClient.get(`${ANALYTICS_BASE}/analytics`, {
      params: { days },
    });
    return response.data;
  },
};

export default analyticsService;
