import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Generate a new learning path
 * @param {Object} data - Learning path parameters
 * @returns {Promise<{task_id: string, status: string, message: string}>}
 */
export const generateLearningPath = async (data) => {
  const response = await api.post('/api/generate', data);
  return response.data;
};

/**
 * Check the status of a task
 * @param {string} taskId - Task ID
 * @returns {Promise<{status: string, progress?: number, message?: string}>}
 */
export const checkTaskStatus = async (taskId) => {
  const response = await api.get(`/api/status/${taskId}`);
  return response.data;
};

/**
 * Get the result of a completed task
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} - Learning path data
 */
export const getTaskResult = async (taskId) => {
  const response = await api.get(`/api/result/${taskId}`);
  return response.data;
};

/**
 * Check API health
 * @returns {Promise<{status: string}>}
 */
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

/**
 * Save the full learning path for the logged-in user.
 * @param {Object} path - The full LearningPath JSON
 * @returns {Promise<{success: boolean, path_id: string}>}
 */
export const saveLearningPath = async (path) => {
  const response = await api.post('/api/save-path', { path });
  return response.data;
};

/**
 * Toggle milestone completion for a saved path.
 * @param {string} pathId
 * @param {number} milestoneIndex
 * @param {boolean} completed
 * @returns {Promise<{success: boolean}>}
 */
export const trackMilestone = async (pathId, milestoneIndex, completed) => {
  const response = await api.post('/api/track-milestone', {
    path_id: pathId,
    milestone_index: milestoneIndex,
    completed,
  });
  return response.data;
};

export default api;
