import React, { useState } from 'react';
import {
  User,
  Globe,
  Bot,
  Shield,
  Save,
  CheckCircle2,
  HardDrive,
  Cpu
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input, { Select } from '../../components/common/Input';
import Badge from '../../components/common/Badge';
import './Settings.css';

export default function Settings() {
  const [userName, setUserName] = useState('Parinitha Reddy');
  const [userEmail, setUserEmail] = useState('demo@ownit.local');
  const [language, setLanguage] = useState('en');
  const [isSaved, setIsSaved] = useState(false);

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
          <Card title="User Profile" subtitle="Your personal information">
            <form onSubmit={handleSave}>
              <Input
                label="Full Name"
                icon={User}
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
              <Input
                label="Email Address"
                type="email"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
              />

              <div style={{ marginTop: '16px' }}>
                <Button type="submit" variant="primary" icon={Save}>
                  Save Changes
                </Button>
                {isSaved && (
                  <span className="save-success-tag">
                    <CheckCircle2 size={16} /> Saved!
                  </span>
                )}
              </div>
            </form>
          </Card>

          <Card title="Language & Localization" subtitle="Select your preferred display language">
            <Select
              label="Interface Language"
              options={languageOptions}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              helperText="Language switching for English, Hindi, and Telugu."
            />
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
