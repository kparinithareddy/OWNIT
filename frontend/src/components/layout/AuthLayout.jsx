import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { Shield, Sparkles } from 'lucide-react';
import './AuthLayout.css';

export default function AuthLayout() {
  return (
    <div className="auth-layout">
      <div className="auth-container">
        <header className="auth-header">
          <Link to="/" className="auth-brand">
            <div className="auth-logo-badge">
              <Shield size={28} />
            </div>
            <div className="auth-brand-info">
              <h1 className="auth-title">OWNIT</h1>
              <p className="auth-tagline">"Own More. Worry Less."</p>
            </div>
          </Link>
          <div className="auth-ai-pill">
            <Sparkles size={14} />
            <span>Smart Product Lifecycle Assistant</span>
          </div>
        </header>

        <main className="auth-card">
          <Outlet />
        </main>

        <footer className="auth-footer">
          <p>&copy; {new Date().getFullYear()} OWNIT &bull; Built with Privacy & Local AI</p>
        </footer>
      </div>
    </div>
  );
}
