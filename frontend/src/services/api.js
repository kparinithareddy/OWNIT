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
    ...(options.headers || {})
  };

  const isFormData = options.body instanceof FormData;
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Attach JWT Bearer token if available
  const token = localStorage.getItem('ownit_token');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let body = options.body;
  if (!isFormData && body && typeof body === 'object') {
    body = JSON.stringify(body);
  }

  const config = {
    ...options,
    headers,
    body
  };

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
  getMe: () => request('/auth/me', { method: 'GET' }),
  updatePreferences: (payload) => request('/auth/preferences', { method: 'PATCH', body: payload })
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
  getTimeline: (id) => request(`/products/${id}/timeline`, { method: 'GET' }),
  addTimelineEvent: (id, payload) => request(`/products/${id}/timeline`, { method: 'POST', body: payload }),
  getLifeScore: (id) => request(`/products/${id}/life-score`, { method: 'GET' }),
  create: (payload) => request('/products/', { method: 'POST', body: payload }),
  update: (id, payload) => request(`/products/${id}`, { method: 'PUT', body: payload }),
  delete: (id) => request(`/products/${id}`, { method: 'DELETE' })
};


// Document Management API methods
export const documentsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.productId && params.productId !== 'All') query.append('productId', params.productId);
    if (params.documentType && params.documentType !== 'All') query.append('documentType', params.documentType);
    const queryStr = query.toString() ? `?${query.toString()}` : '';
    return request(`/documents/${queryStr}`, { method: 'GET' });
  },
  get: (id) => request(`/documents/${id}`, { method: 'GET' }),
  upload: (formData) => request('/documents/upload', { method: 'POST', body: formData }),
  delete: (id) => request(`/documents/${id}`, { method: 'DELETE' }),
  viewFile: async (id, download = false) => {
    const token = localStorage.getItem('ownit_token');
    const url = `${API_V1_URL}/documents/${id}/download?download=${download}`;
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    if (!response.ok) {
      throw new ApiError('Failed to retrieve document file', response.status);
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    return objectUrl;
  }
};

// Receipt OCR API methods
export const ocrApi = {
  scan: (formData) => request('/ocr/scan', { method: 'POST', body: formData }),
  confirm: (payload) => request('/ocr/confirm', { method: 'POST', body: payload })
};

// Warranty Management API methods
export const warrantiesApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.productId && params.productId !== 'All') query.append('productId', params.productId);
    if (params.status && params.status !== 'All') query.append('status', params.status);
    const queryStr = query.toString() ? `?${query.toString()}` : '';
    return request(`/warranties/${queryStr}`, { method: 'GET' });
  },
  get: (id) => request(`/warranties/${id}`, { method: 'GET' }),
  getByProduct: (productId) => request(`/warranties/product/${productId}`, { method: 'GET' }),
  getSummary: () => request('/warranties/summary', { method: 'GET' }),
  create: (payload) => request('/warranties/', { method: 'POST', body: payload }),
  update: (id, payload) => request(`/warranties/${id}`, { method: 'PUT', body: payload }),
  delete: (id) => request(`/warranties/${id}`, { method: 'DELETE' })
};

// In-App Notification API methods
export const notificationsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.unreadOnly) query.append('unread_only', 'true');
    if (params.limit) query.append('limit', String(params.limit));
    const queryStr = query.toString() ? `?${query.toString()}` : '';
    return request(`/notifications/${queryStr}`, { method: 'GET' });
  },
  getUnreadCount: () => request('/notifications/unread-count', { method: 'GET' }),
  markAsRead: (id) => request(`/notifications/${id}/read`, { method: 'PUT' }),
  markAllAsRead: () => request('/notifications/mark-all-read', { method: 'POST' }),
  triggerCheck: () => request('/notifications/trigger-check', { method: 'POST' }),
  delete: (id) => request(`/notifications/${id}`, { method: 'DELETE' })
};

// Product Maintenance API methods
export const maintenanceApi = {
  listByProduct: (productId) => request(`/maintenance/product/${productId}`, { method: 'GET' }),
  getRecommendations: (productId) => request(`/maintenance/product/${productId}/recommendations`, { method: 'GET' }),
  get: (id) => request(`/maintenance/${id}`, { method: 'GET' }),
  create: (payload) => request('/maintenance/', { method: 'POST', body: payload }),
  update: (id, payload) => request(`/maintenance/${id}`, { method: 'PUT', body: payload }),
  delete: (id) => request(`/maintenance/${id}`, { method: 'DELETE' })
};

// Local AI (Ollama) API methods
export const aiApi = {
  getStatus: () => request('/ai/status', { method: 'GET' }),
  testPrompt: (payload) => request('/ai/test', { method: 'POST', body: payload }),
  getChatHistory: (productId) => request(`/ai/chat/${productId}`, { method: 'GET' }),
  sendMessage: (payload) => request('/ai/chat', { method: 'POST', body: payload }),
  clearChatHistory: (productId) => request(`/ai/chat/${productId}`, { method: 'DELETE' })
};

// Warranty Intelligence API methods
export const warrantyIntelligenceApi = {
  analyze: (payload) => request('/warranty-intelligence/analyze', { method: 'POST', body: payload }),
  quickCheck: (productId, questionType = 'is_active') =>
    request(`/warranty-intelligence/quick-check/${productId}?questionType=${questionType}`, { method: 'GET' })
};

// Warranty Claim Assistant API methods
export const claimAssistantApi = {
  prepare: (payload) => request('/claim-assistant/prepare', { method: 'POST', body: payload })
};

// Service History API methods
export const servicesApi = {
  listByProduct: (productId) => request(`/services/product/${productId}`, { method: 'GET' }),
  get: (id) => request(`/services/${id}`, { method: 'GET' }),
  create: (payload) => request('/services/', { method: 'POST', body: payload }),
  update: (id, payload) => request(`/services/${id}`, { method: 'PUT', body: payload }),
  delete: (id) => request(`/services/${id}`, { method: 'DELETE' })
};

// Compatible Accessory Recommendations API methods
export const accessoriesApi = {
  getRecommendations: (params = {}) => {
    const query = new URLSearchParams();
    if (params.productId) query.append('productId', params.productId);
    if (params.category && params.category !== 'All') query.append('category', params.category);
    if (params.minBudget !== undefined && params.minBudget !== null && params.minBudget !== '') query.append('minBudget', params.minBudget);
    if (params.maxBudget !== undefined && params.maxBudget !== null && params.maxBudget !== '') query.append('maxBudget', params.maxBudget);
    return request(`/accessories/recommendations?${query.toString()}`, { method: 'GET' });
  },
  getCategories: (productId) => request(`/accessories/categories?productId=${productId}`, { method: 'GET' })
};

// Safety & Recall Alerts API methods
export const recallsApi = {
  checkProduct: (productId) => request(`/safety-recalls/check/${productId}`, { method: 'GET' }),
  vaultScan: () => request('/safety-recalls/vault-scan', { method: 'GET' })
};








