import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  FileText,
  ShieldCheck,
  Bot,
  PlugZap,
  Bell,
  Settings,
  X
} from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';
import './Sidebar.css';

export default function Sidebar({ isOpen, onClose }) {
  const { t } = useLanguage();

  const navGroups = [
    {
      title: t('nav.overview', {}, 'Overview'),
      items: [
        { name: t('nav.dashboard', {}, 'Dashboard'), path: '/dashboard', icon: LayoutDashboard }
      ]
    },
    {
      title: t('nav.inventoryRecords', {}, 'Inventory & Records'),
      items: [
        { name: t('nav.products', {}, 'Products'), path: '/products', icon: Package },
        { name: t('nav.documents', {}, 'Documents'), path: '/documents', icon: FileText },
        { name: t('nav.warrantyTracker', {}, 'Warranty Tracker'), path: '/warranty', icon: ShieldCheck }
      ]
    },
    {
      title: t('nav.intelligence', {}, 'Intelligence'),
      items: [
        { name: t('nav.aiAssistant', {}, 'AI Assistant'), path: '/ai-assistant', icon: Bot, isNew: true },
        { name: t('nav.accessories', {}, 'Accessories'), path: '/accessories', icon: PlugZap }
      ]
    },
    {
      title: t('nav.system', {}, 'System'),
      items: [
        { name: t('nav.notifications', {}, 'Notifications'), path: '/notifications', icon: Bell },
        { name: t('nav.settings', {}, 'Settings'), path: '/settings', icon: Settings }
      ]
    }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-mobile-header">
          <span className="sidebar-mobile-title">{t('nav.inventoryRecords', {}, 'Navigation')}</span>
          <button className="sidebar-close-btn" onClick={onClose} aria-label="Close Sidebar">
            <X size={20} />
          </button>
        </div>

        <div className="sidebar-scrollable">
          {navGroups.map((group, groupIdx) => (
            <div key={groupIdx} className="sidebar-group">
              <div className="sidebar-group-title">{group.title}</div>
              <nav className="sidebar-nav">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => {
                        // Close sidebar on mobile when navigating
                        if (window.innerWidth <= 768) {
                          onClose();
                        }
                      }}
                      className={({ isActive }) =>
                        `sidebar-link ${isActive ? 'sidebar-link-active' : ''}`
                      }
                    >
                      <Icon size={18} className="sidebar-link-icon" />
                      <span className="sidebar-link-text">{item.name}</span>
                      {item.isNew && <span className="sidebar-tag-new">AI</span>}
                      {item.badge && <span className="sidebar-badge">{item.badge}</span>}
                    </NavLink>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        {/* Local AI status pill in sidebar footer */}
        <div className="sidebar-footer">
          <div className="sidebar-status-box">
            <div className="status-indicator-dot" />
            <div className="status-text-box">
              <span className="status-title">{t('nav.ollamaEngine', {}, 'Ollama Engine')}</span>
              <span className="status-subtitle">{t('nav.localPrivate', {}, 'Local & Private')}</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

