import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import Button from './Button';
import './StateScreens.css';

export default function ErrorState({
  title = 'Something went wrong',
  description = 'An error occurred while loading this section. Please try again.',
  onRetry,
  retryLabel = 'Try Again',
  className = ''
}) {
  return (
    <div className={`state-container error-state ${className}`}>
      <div className="state-icon-wrapper state-icon-danger">
        <AlertCircle size={36} />
      </div>
      <h4 className="state-title">{title}</h4>
      <p className="state-desc">{description}</p>
      {onRetry && (
        <div className="state-action">
          <Button variant="outline" icon={RotateCcw} onClick={onRetry}>
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
