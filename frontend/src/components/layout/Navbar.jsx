import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Menu,
  Bell,
  Search,
  Shield,
  User,
  Sparkles,
  LogOut,
  Globe
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './Navbar.css';

export default function Navbar({ onToggleSidebar }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const displayLanguage = (user?.preferredLanguage || 'en').toUpperCase();

  return (
    <header className="navbar">
      <div className="navbar-left">
        <button
          className="navbar-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle Navigation Menu"
        >
          <Menu size={20} />
        </button>

        <Link to="/dashboard" className="navbar-brand">
          <div className="navbar-logo-badge">
            <Shield size={20} className="navbar-logo-icon" />
          </div>
          <div className="navbar-brand-text">
            <span className="navbar-brand-name">OWNIT</span>
            <span className="navbar-brand-tagline">Own More. Worry Less.</span>
          </div>
        </Link>
      </div>

      <div className="navbar-center">
        <div className="navbar-search">
          <Search size={16} className="navbar-search-icon" />
          <input
            type="text"
            placeholder="Search products, receipts, warranties (Press '/' to search)"
            className="navbar-search-input"
            onClick={() => navigate('/products')}
          />
        </div>
      </div>

      <div className="navbar-right">
        {/* Quick Local AI Trigger */}
        <Link to="/ai-assistant" className="navbar-ai-chip" title="Local AI Assistant">
          <Sparkles size={14} />
          <span>Ask AI</span>
        </Link>

        {/* Notifications Icon with Badge */}
        <Link to="/notifications" className="navbar-icon-btn" title="Notifications & Expiration Alerts">
          <Bell size={18} />
          <span className="navbar-notification-dot" />
        </Link>

        {/* Language Indicator */}
        <Link to="/settings" className="navbar-lang-badge" title="Language settings">
          <Globe size={14} />
          <span>{displayLanguage}</span>
        </Link>

        {/* User Profile avatar */}
        <div className="navbar-user-profile">
          <div className="navbar-avatar">
            <User size={16} />
          </div>
          <div className="navbar-user-info">
            <span className="navbar-user-name">{user?.username || 'User'}</span>
            <span className="navbar-user-role">Account Active</span>
          </div>
          <button
            className="navbar-logout-btn"
            onClick={handleLogout}
            title="Log Out"
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
