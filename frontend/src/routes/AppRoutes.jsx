import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import AppLayout from '../components/layout/AppLayout';
import AuthLayout from '../components/layout/AuthLayout';

// Route Guards
import { ProtectedRoute, PublicOnlyRoute } from '../components/common/ProtectedRoute';

// Pages
import Login from '../pages/auth/Login';
import Signup from '../pages/auth/Signup';
import Dashboard from '../pages/dashboard/Dashboard';
import ProductList from '../pages/products/ProductList';
import ProductDetail from '../pages/products/ProductDetail';
import Documents from '../pages/documents/Documents';
import WarrantyTracker from '../pages/warranty/WarrantyTracker';
import AIAssistant from '../pages/ai/AIAssistant';
import Accessories from '../pages/accessories/Accessories';
import Notifications from '../pages/notifications/Notifications';
import Settings from '../pages/settings/Settings';
import NotFound from '../pages/NotFound';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Authentication Routes (Redirect to /dashboard if already logged in) */}
      <Route element={<PublicOnlyRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Route>
      </Route>

      {/* Protected Routes (Redirect to /login if not authenticated) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/products" element={<ProductList />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/warranty" element={<WarrantyTracker />} />
          <Route path="/ai-assistant" element={<AIAssistant />} />
          <Route path="/accessories" element={<Accessories />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>

      {/* Fallback 404 Route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
