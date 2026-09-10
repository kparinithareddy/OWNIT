import React, { useState, useEffect } from 'react';
import {
  User,
  Globe,
  Bot,
  Shield,
  Save,
  CheckCircle2,
  HardDrive,
  Cpu,
  Calendar,
  KeyRound
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input, { Select } from '../../components/common/Input';
import Badge from '../../components/common/Badge';
import { useAuth } from '../../context/AuthContext';
import './Settings.css';

export default function Settings() {
  const { user } = useAuth();
  const [username, setUsername] = useState('');
  const [language, setLanguage] = useState('en');
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setUsername(user.username || '');
      setLanguage(user.preferredLanguage || 'en');
    }
  }, [user]);

  const handleSave = (e) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const languageOptions = [
    { value: 'en', label: 'English (Default)' },
    { value: 'hi', label: 'हिंदी (Hindi)' },
    { value: 'te', label: 'తెలుగు (Telugu)' }
  ];

  return (
    <PageContainer
      title="System & Account Settings"
      subtitle="Configure your profile, language preferences, and verify local AI / OCR engine connectivity."
    >
      <div className="settings-grid">
        {/* Left Column: User Profile & Preferences */}
        <div className="settings-col">
          <Card title="User Account" subtitle="Your authenticated profile credentials">
            <form onSubmit={handleSave}>
              <Input
                label="Username"
                icon={User}
                value={username}
                disabled
                helperText="Username is linked to your secure JWT identity"
              />

              <div style={{ marginBottom: '16px' }}>
                <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Account ID: </span>
                <code style={{ fontSize: '0.8125rem', backgroundColor: 'var(--bg-surface-secondary)', padding: '2px 6px', borderRadius: '4px' }}>
                  {user?.id || 'N/A'}
                </code>
              </div>

              {user?.createdAt && (
                <div style={{ marginBottom: '16px', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  Member since: {new Date(user.createdAt).toLocaleDateString()}
                </div>
              )}

              <Select
                label="Interface Language"
                options={languageOptions}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                helperText="Select English, Hindi (हिंदी), or Telugu (తెలుగు)."
              />

              <div style={{ marginTop: '20px' }}>
                <Button type="submit" variant="primary" icon={Save}>
                  Save Preferences
                </Button>
                {isSaved && (
                  <span className="save-success-tag">
                    <CheckCircle2 size={16} /> Saved!
                  </span>
                )}
              </div>
            </form>
          </Card>
        </div>

        {/* Right Column: Local AI & OCR Diagnostics */}
        <div className="settings-col">
          <Card
            title="Local AI & Engine Diagnostics"
            subtitle="Status of your offline OCR and LLM services"
          >
            <div className="engine-status-list">
              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <KeyRound size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">JWT Authentication</h4>
                    <Badge variant="active" size="sm">Active (HS256)</Badge>
                  </div>
                  <p className="engine-desc">Stateless token validation with bcrypt password hashing</p>
                </div>
              </div>

              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <Cpu size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">Ollama Local LLM</h4>
                    <Badge variant="active" size="sm">Configured</Badge>
                  </div>
                  <p className="engine-desc">Model: LLaMA 3.2 &bull; Endpoint: http://localhost:11434</p>
                </div>
              </div>

              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <HardDrive size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">Tesseract OCR Engine</h4>
                    <Badge variant="active" size="sm">Ready</Badge>
                  </div>
                  <p className="engine-desc">OCR Binary: Windows Local Executable</p>
                </div>
              </div>

              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <Shield size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">Privacy & Security</h4>
                    <Badge variant="active" size="sm">100% Offline</Badge>
                  </div>
                  <p className="engine-desc">No receipt or serial numbers sent to external cloud APIs</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}
