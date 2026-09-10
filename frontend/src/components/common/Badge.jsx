import React from 'react';
import './Badge.css';

export default function Badge({
  children,
  variant = 'neutral', // 'active' | 'warning' | 'danger' | 'info' | 'neutral'
  dot = false,
  size = 'md',        // 'sm' | 'md'
  className = ''
}) {
  return (
    <span className={`badge badge-${variant} badge-${size} ${className}`}>
      {dot && <span className="badge-dot" />}
      {children}
    </span>
  );
}
