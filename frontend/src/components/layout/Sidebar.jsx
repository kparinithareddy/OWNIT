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
import './Sidebar.css';

const navGroups = [
  {
    title: 'Overview',
    items: [
      { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard }
    ]
  },
  {
    title: 'Inventory & Records',
    items: [
      { name: 'Products', path: '/products', icon: Package, badge: '5' },
      { name: 'Documents', path: '/documents', icon: FileText, badge: '8' },
      { name: 'Warranty Tracker', path: '/warranty', icon: ShieldCheck, badge: '2 Due' }
    ]
  },
  {
    title: 'Intelligence',
    items: [
      { name: 'AI Assistant', path: '/ai-assistant', icon: Bot, isNew: true },
      { name: 'Accessories', path: '/accessories', icon: PlugZap }
    ]
  },
  {
    title: 'System',
    items: [
      { name: 'Notifications', path: '/notifications', icon: Bell, badge: '3' },
      { name: 'Settings', path: '/settings', icon: Settings }
    ]
  }
];

export default function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-mobile-header">
          <span className="sidebar-mobile-title">Navigation</span>
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
              <span className="status-title">Ollama Engine</span>
              <span className="status-subtitle">Local & Private</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
