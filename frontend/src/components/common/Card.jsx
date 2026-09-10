import React from 'react';
import './Card.css';

export default function Card({
  children,
  title,
  subtitle,
  action,
  className = '',
  hoverable = false,
  padding = 'md', // 'none' | 'sm' | 'md' | 'lg'
  onClick,
  ...rest
}) {
  return (
    <div
      className={`card ${hoverable ? 'card-hoverable' : ''} card-p-${padding} ${className}`}
      onClick={onClick}
      {...rest}
    >
      {(title || subtitle || action) && (
        <div className="card-header">
          <div className="card-header-titles">
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {action && <div className="card-header-action">{action}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'primary', // 'primary' | 'success' | 'warning' | 'info' | 'danger'
  trend,
  className = ''
}) {
  return (
    <div className={`card stat-card stat-${variant} ${className}`}>
      <div className="stat-content">
        <p className="stat-title">{title}</p>
        <p className="stat-value">{value}</p>
        {subtitle && <p className="stat-subtitle">{subtitle}</p>}
        {trend && <p className="stat-trend">{trend}</p>}
      </div>
      {Icon && (
        <div className={`stat-icon-wrapper stat-icon-${variant}`}>
          <Icon size={24} />
        </div>
      )}
    </div>
  );
}
