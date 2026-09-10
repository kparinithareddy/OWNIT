/**
 * Centralized API client service for OWNIT frontend.
 * Automatically attaches JWT Bearer token from localStorage to outgoing requests.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1_URL = `${API_BASE_URL}/api/v1`;

export class ApiError extends Error {
  constructor(message, status, code, details) {
    super(message);
    this.status = status;
    this.code = code || 'API_ERROR';
    this.details = details || null;
  }
}

export async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_V1_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  // Attach JWT Bearer token if available
  const token = localStorage.getItem('ownit_token');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    let data = null;
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    }

    if (!response.ok) {
      let errorMessage = 'A network error occurred. Please try again.';
      let errorCode = `HTTP_${response.status}`;
      let errorDetails = null;

      if (data && data.error) {
        errorMessage = data.error.message || errorMessage;
        errorCode = data.error.code || errorCode;
        errorDetails = data.error.details || null;
      } else if (data && data.detail) {
        errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }

      throw new ApiError(errorMessage, response.status, errorCode, errorDetails);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network or offline error
    throw new ApiError(
      'Unable to connect to OWNIT backend service. Please ensure the server is running.',
      0,
      'NETWORK_ERROR'
    );
  }
}

// Authentication API methods
export const authApi = {
  signup: (payload) => request('/auth/signup', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),
  getMe: () => request('/auth/me', { method: 'GET' })
};

// Product Management API methods
export const productsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.category && params.category !== 'All') query.append('category', params.category);
    if (params.search && params.search.trim()) query.append('search', params.search.trim());
    const queryStr = query.toString() ? `?${query.toString()}` : '';
    return request(`/products/${queryStr}`, { method: 'GET' });
  },
  get: (id) => request(`/products/${id}`, { method: 'GET' }),
  create: (payload) => request('/products/', { method: 'POST', body: payload }),
  update: (id, payload) => request(`/products/${id}`, { method: 'PUT', body: payload }),
  delete: (id) => request(`/products/${id}`, { method: 'DELETE' })
};
