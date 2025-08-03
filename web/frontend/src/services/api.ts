import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Health check
  healthCheck: async () => {
    const response = await axiosInstance.get('/api/health');
    return response.data;
  },

  // Career Database
  getCareerDatabase: async () => {
    const response = await axiosInstance.get('/api/database');
    return response.data;
  },

  buildCareerDatabase: async (data: { documents_directory: string }) => {
    const response = await axiosInstance.post('/api/database/build', data);
    return response.data;
  },

  // Job Analysis
  analyzeJob: async (data: { job_url: string; job_description?: string }) => {
    const response = await axiosInstance.post('/api/jobs/analyze', data);
    return response.data;
  },

  getJobAnalysis: async (jobId: string) => {
    const response = await axiosInstance.get(`/api/jobs/${jobId}`);
    return response.data;
  },

  // Document Generation
  generateDocument: async (data: {
    job_url: string;
    job_title?: string;
    company_name?: string;
    document_type: 'cv' | 'cover_letter';
    template?: string;
    tone?: string;
  }) => {
    const response = await axiosInstance.post('/api/documents/generate', data);
    return response.data;
  },

  getDocument: async (documentId: string) => {
    const response = await axiosInstance.get(`/api/documents/${documentId}`);
    return response.data;
  },

  // Workflows
  getWorkflowStatus: async (workflowId: string) => {
    const response = await axiosInstance.get(`/api/workflows/${workflowId}/status`);
    return response.data;
  },

  listWorkflows: async () => {
    const response = await axiosInstance.get('/api/workflows');
    return response.data;
  },

  // File Upload
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axiosInstance.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default api;