import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi, ApiError } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('ownit_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('ownit_token') || null);
  const [loading, setLoading] = useState(true);

  // Validate and refresh user profile on initial load if token exists
  useEffect(() => {
    async function checkAuth() {
      const storedToken = localStorage.getItem('ownit_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const userProfile = await authApi.getMe();
        setUser(userProfile);
        localStorage.setItem('ownit_user', JSON.stringify(userProfile));
      } catch (err) {
        console.warn('Session expired or invalid token:', err.message);
        logout();
      } finally {
        setLoading(false);
      }
    }

    checkAuth();
  }, []);

  const login = async (username, password) => {
    const data = await authApi.login({ username, password });
    const { accessToken, user: userData } = data;

    localStorage.setItem('ownit_token', accessToken);
    localStorage.setItem('ownit_user', JSON.stringify(userData));

    setToken(accessToken);
    setUser(userData);
    return userData;
  };

  const signup = async (username, password, confirmPassword, preferredLanguage = 'en') => {
    const data = await authApi.signup({
      username,
      password,
      confirmPassword,
      preferredLanguage
    });
    const { accessToken, user: userData } = data;

    localStorage.setItem('ownit_token', accessToken);
    localStorage.setItem('ownit_user', JSON.stringify(userData));

    setToken(accessToken);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('ownit_token');
    localStorage.removeItem('ownit_user');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    loading,
    login,
    signup,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
