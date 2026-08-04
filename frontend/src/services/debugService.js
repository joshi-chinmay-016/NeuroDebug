/**
 * Debug Service
 * Service for debug-related API calls.
 */

import apiClient from './api';

/**
 * Run debug analysis on Python code.
 * @param {string} code - Python code to analyze
 * @param {string} apiKey - Optional Groq API key
 * @returns {Promise<Object>} Debug response with analysis and patch
 */
export async function runDebug(code, apiKey) {
  const body = { code };
  if (apiKey && apiKey.trim()) {
    body.api_key = apiKey.trim();
  }
  const response = await apiClient.post('/debug', body);
  return response.data;
}

/**
 * Check API health status.
 * @returns {Promise<Object>} Health status
 */
export async function checkHealth() {
  const response = await apiClient.get('/health');
  return response.data;
}
