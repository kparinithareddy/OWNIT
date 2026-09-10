import React from 'react';
import './PageContainer.css';

export default function PageContainer({
  title,
  subtitle,
  badge,
  actions,
  children,
  maxWidth = '1200px',
  className = ''
}) {
  return (
    <div className={`page-container ${className}`} style={{ maxWidth }}>
      {(title || subtitle || actions || badge) && (
        <div className="page-header">
          <div className="page-header-text">
            {badge && <div className="page-header-badge">{badge}</div>}
            {title && <h1 className="page-title">{title}</h1>}
            {subtitle && <p className="page-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="page-actions">{actions}</div>}
        </div>
      )}
      <div className="page-content">{children}</div>
    </div>
  );
}
