import React from 'react';
import { Loader2 } from 'lucide-react';
import './StateScreens.css';

export default function LoadingState({
  message = 'Loading data...',
  description = 'Please wait while we fetch your information',
  fullscreen = false
}) {
  return (
    <div className={`state-container ${fullscreen ? 'state-fullscreen' : ''}`}>
      <div className="state-spinner-wrapper">
        <Loader2 className="state-spinner" size={36} />
      </div>
      <h4 className="state-title">{message}</h4>
      {description && <p className="state-desc">{description}</p>}
    </div>
  );
}
