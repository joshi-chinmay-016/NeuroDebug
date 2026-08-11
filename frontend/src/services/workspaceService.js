/**
 * Workspace Service
 * Handles all workspace and project-related API calls.
 */

import apiClient from './api';

const WORKSPACE_BASE = '/workspace';

export const workspaceService = {
  /**
   * Create a new project
   */
  async createProject(name, description = null) {
    const response = await apiClient.post(`${WORKSPACE_BASE}/projects`, {
      name,
      description,
    });
    return response.data;
  },

  /**
   * List all projects for the user
   */
  async listProjects(skip = 0, limit = 50, includeArchived = false) {
    const response = await apiClient.get(`${WORKSPACE_BASE}/projects`, {
      params: {
        skip,
        limit,
        include_archived: includeArchived,
      },
    });
    return response.data;
  },

  /**
   * Get a specific project
   */
  async getProject(projectId) {
    const response = await apiClient.get(`${WORKSPACE_BASE}/projects/${projectId}`);
    return response.data;
  },

  /**
   * Update a project
   */
  async updateProject(projectId, name = null, description = null) {
    const response = await apiClient.patch(`${WORKSPACE_BASE}/projects/${projectId}`, {
      name,
      description,
    });
    return response.data;
  },

  /**
   * Archive (soft delete) a project
   */
  async archiveProject(projectId) {
    const response = await apiClient.delete(`${WORKSPACE_BASE}/projects/${projectId}`);
    return response.data;
  },

  /**
   * Restore a previously archived project
   */
  async restoreProject(projectId) {
    const response = await apiClient.post(`${WORKSPACE_BASE}/projects/${projectId}/restore`);
    return response.data;
  },
};

export default workspaceService;
