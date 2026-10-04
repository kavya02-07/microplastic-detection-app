const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Custom API Client using native fetch.
 * Automatically handles Authorization headers, JSON/FormData formatting, and error parsing.
 */
async function request(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  
  const headers = {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  // Only set application/json if body is NOT FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
  };

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  let data;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMessage = typeof data === 'object' && data.detail
      ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
      : `Error ${response.status}: ${response.statusText}`;
    
    const error = new Error(errorMessage);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const authAPI = {
  login: (email, password) => request('/auth/login', {
    method: 'POST',
    body: { email, password },
  }),

  register: (email, password) => request('/auth/register', {
    method: 'POST',
    body: { email, password },
  }),

  getCurrentUser: () => request('/auth/me', {
    method: 'GET',
  }),
};

export const detectionAPI = {
  detect: (file, confidence = 0.40) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('confidence', confidence);

    return request('/detect', {
      method: 'POST',
      body: formData,
    });
  },
};

export const analysesAPI = {
  list: (skip = 0, limit = 100) => request(`/analyses?skip=${skip}&limit=${limit}`, {
    method: 'GET',
  }),

  getById: (id) => request(`/analyses/${id}`, {
    method: 'GET',
  }),
};

export const modelAPI = {
  getEvaluation: () => request('/model/evaluation', {
    method: 'GET',
  }),
};

export const reportsAPI = {
  downloadReport: async (analysisId) => {
    const token = localStorage.getItem('token');
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

    const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}/report`, {
      method: 'GET',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      let errorMessage = `Error ${response.status}: ${response.statusText}`;
      try {
        const errData = await response.json();
        if (errData.detail) {
          errorMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        }
      } catch { /* ignore parse errors */ }
      const error = new Error(errorMessage);
      error.status = response.status;
      throw error;
    }

    const blob = await response.blob();
    return blob;
  },
};

export default request;

