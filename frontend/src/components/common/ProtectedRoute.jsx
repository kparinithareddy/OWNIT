import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingState from './LoadingState';

export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingState message="Verifying authentication..." fullscreen />;
  }

  if (!isAuthenticated) {
    // Redirect unauthenticated user to login, preserving intended destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingState message="Loading..." fullscreen />;
  }

  if (isAuthenticated) {
    // Already logged in users are redirected to dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
