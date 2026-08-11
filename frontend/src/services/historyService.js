/**
 * History Service
 * Handles all debug history-related API calls.
 */

import apiClient from './api';

const HISTORY_BASE = '/history';

export const historyService = {
  /**
   * List debug sessions
   */
  async listSessions(skip = 0, limit = 50, projectId = null) {
    const params = { skip, limit };
    if (projectId) {
      params.project_id = projectId;
    }
    const response = await apiClient.get(`${HISTORY_BASE}/sessions`, { params });
    return response.data;
  },

  /**
   * Get a specific debug session with full details
   */
  async getSession(sessionId) {
    const response = await apiClient.get(`${HISTORY_BASE}/sessions/${sessionId}`);
    return response.data;
  },

  /**
   * Export a debug session
   */
  async exportSession(sessionId, format = 'json') {
    const response = await apiClient.get(
      `${HISTORY_BASE}/sessions/${sessionId}/export`,
      { params: { format } }
    );
    return response.data;
  },
};

export default historyService;
