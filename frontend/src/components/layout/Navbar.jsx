import React, { useState, useEffect } from 'react';
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
import { useLanguage } from '../../i18n/LanguageContext';
import { notificationsApi } from '../../services/api';
import './Navbar.css';

export default function Navbar({ onToggleSidebar }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { language, changeLanguage, t } = useLanguage();
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchUnread = async () => {
    try {
      if (user) {
        const data = await notificationsApi.getUnreadCount();
        setUnreadCount(data.unreadCount || 0);
      }
    } catch (err) {
      console.debug('Failed to fetch unread notification count:', err);
    }
  };

  useEffect(() => {
    fetchUnread();
    // Poll unread count periodically every 60 seconds
    const interval = setInterval(fetchUnread, 60000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleLanguageCycle = (e) => {
    e.preventDefault();
    const cycleMap = { en: 'hi', hi: 'te', te: 'en' };
    const nextLang = cycleMap[language] || 'en';
    changeLanguage(nextLang);
  };

  const displayLanguage = language.toUpperCase();

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
            <span className="navbar-brand-name">{t('common.appName', {}, 'OWNIT')}</span>
            <span className="navbar-brand-tagline">{t('common.tagline', {}, 'Own More. Worry Less.')}</span>
          </div>
        </Link>
      </div>

      <div className="navbar-center">
        <div className="navbar-search">
          <Search size={16} className="navbar-search-icon" />
          <input
            type="text"
            placeholder={t('nav.searchPlaceholder', {}, "Search products, receipts, warranties (Press '/' to search)")}
            className="navbar-search-input"
            onClick={() => navigate('/products')}
          />
        </div>
      </div>

      <div className="navbar-right">
        {/* Quick Local AI Trigger */}
        <Link to="/ai-assistant" className="navbar-ai-chip" title={t('nav.aiAssistant', {}, 'Local AI Assistant')}>
          <Sparkles size={14} />
          <span>{t('nav.askAi', {}, 'Ask AI')}</span>
        </Link>

        {/* Notifications Icon with Dynamic Badge */}
        <Link to="/notifications" className="navbar-icon-btn" title={t('nav.notifications', {}, 'Notifications & Expiration Alerts')}>
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="navbar-notification-badge" title={`${unreadCount} unread notification(s)`}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Link>

        {/* Quick Language Toggle Button */}
        <button
          onClick={handleLanguageCycle}
          className="navbar-lang-badge"
          title={`Current: ${displayLanguage}. Click to toggle English / Hindi / Telugu.`}
          style={{ background: 'none', border: '1px solid var(--border-color)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          <Globe size={14} />
          <span>{displayLanguage}</span>
        </button>

        {/* User Profile avatar */}
        <div className="navbar-user-profile">
          <div className="navbar-avatar">
            <User size={16} />
          </div>
          <div className="navbar-user-info">
            <span className="navbar-user-name">{user?.username || 'User'}</span>
            <span className="navbar-user-role">{t('nav.accountActive', {}, 'Account Active')}</span>
          </div>
          <button
            className="navbar-logout-btn"
            onClick={handleLogout}
            title={t('nav.logout', {}, 'Log Out')}
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}

