import React from 'react';
import { PackageOpen } from 'lucide-react';
import Button from './Button';
import './StateScreens.css';

export default function EmptyState({
  title = 'No items found',
  description = 'You have not added any items to this section yet.',
  icon: Icon = PackageOpen,
  actionLabel,
  onAction,
  className = ''
}) {
  return (
    <div className={`state-container empty-state ${className}`}>
      <div className="state-icon-wrapper state-icon-neutral">
        <Icon size={36} />
      </div>
      <h4 className="state-title">{title}</h4>
      <p className="state-desc">{description}</p>
      {actionLabel && onAction && (
        <div className="state-action">
          <Button variant="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
