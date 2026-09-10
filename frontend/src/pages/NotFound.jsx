import React from 'react';
import { useNavigate } from 'react-router-dom';
import { HelpCircle, Home, ArrowLeft } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Button from '../components/common/Button';
import './NotFound.css';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <PageContainer>
      <div className="not-found-container">
        <div className="not-found-badge">404 Error</div>
        <h2 className="not-found-title">Page Not Found</h2>
        <p className="not-found-desc">
          The page you are looking for doesn't exist or has been moved. Let's get you back to your assets.
        </p>
        <div className="not-found-actions">
          <Button
            variant="primary"
            icon={Home}
            onClick={() => navigate('/dashboard')}
          >
            Go to Dashboard
          </Button>
          <Button
            variant="outline"
            icon={ArrowLeft}
            onClick={() => navigate(-1)}
          >
            Go Back
          </Button>
        </div>
      </div>
    </PageContainer>
  );
}
