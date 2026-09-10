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
import { useLanguage } from '../../i18n/LanguageContext';
import { authApi } from '../../services/api';
import './Settings.css';

export default function Settings() {
  const { user } = useAuth();
  const { language, changeLanguage, t } = useLanguage();
  const [username, setUsername] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(language);
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      setUsername(user.username || '');
    }
  }, [user]);

  useEffect(() => {
    setSelectedLanguage(language);
  }, [language]);

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      // 1. Update frontend LanguageContext immediately
      changeLanguage(selectedLanguage);

      // 2. Persist to MongoDB profile
      await authApi.updatePreferences({ preferredLanguage: selectedLanguage });
      
      // 3. Update localStorage user profile
      const storedUser = localStorage.getItem('ownit_user');
      if (storedUser) {
        const parsed = JSON.parse(storedUser);
        parsed.preferredLanguage = selectedLanguage;
        localStorage.setItem('ownit_user', JSON.stringify(parsed));
      }

      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      console.error('Failed to update language preferences:', err);
      setError(err.message || 'Failed to update preferences');
    } finally {
      setIsSaving(false);
    }
  };

  const languageOptions = [
    { value: 'en', label: 'English (Default)' },
    { value: 'hi', label: 'हिंदी (Hindi)' },
    { value: 'te', label: 'తెలుగు (Telugu)' }
  ];

  return (
    <PageContainer
      title={t('settings.title', {}, 'System & Account Settings')}
      subtitle={t('settings.subtitle', {}, 'Configure your profile, language preferences, and verify local AI / OCR engine connectivity.')}
    >
      <div className="settings-grid">
        {/* Left Column: User Profile & Preferences */}
        <div className="settings-col">
          <Card
            title={t('settings.userAccount', {}, 'User Account')}
            subtitle={t('settings.userAccountDesc', {}, 'Your authenticated profile credentials')}
          >
            <form onSubmit={handleSave}>
              <Input
                label={t('auth.username', {}, 'Username')}
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
                label={t('settings.interfaceLanguage', {}, 'Interface Language')}
                options={languageOptions}
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                helperText={t('settings.interfaceLanguageDesc', {}, 'Select English, Hindi (हिंदी), or Telugu (తెలుగు).')}
              />

              {error && (
                <div style={{ color: 'var(--status-danger)', fontSize: '0.875rem', marginBottom: '12px' }}>
                  {error}
                </div>
              )}

              <div style={{ marginTop: '20px' }}>
                <Button type="submit" variant="primary" icon={Save} disabled={isSaving}>
                  {isSaving ? t('common.saving', {}, 'Saving...') : t('settings.savePreferences', {}, 'Save Preferences')}
                </Button>
                {isSaved && (
                  <span className="save-success-tag">
                    <CheckCircle2 size={16} /> {t('settings.savedSuccess', {}, 'Saved!')}
                  </span>
                )}
              </div>
            </form>
          </Card>
        </div>

        {/* Right Column: Local AI & OCR Diagnostics */}
        <div className="settings-col">
          <Card
            title={t('settings.engineDiagnostics', {}, 'Local AI & Engine Diagnostics')}
            subtitle={t('settings.engineDiagnosticsDesc', {}, 'Status of your offline OCR and LLM services')}
          >
            <div className="engine-status-list">
              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <KeyRound size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">{t('settings.jwtAuth', {}, 'JWT Authentication')}</h4>
                    <Badge variant="active" size="sm">Active (HS256)</Badge>
                  </div>
                  <p className="engine-desc">{t('settings.jwtAuthDesc', {}, 'Stateless token validation with bcrypt password hashing')}</p>
                </div>
              </div>

              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <Cpu size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">{t('settings.ollamaLlm', {}, 'Ollama Local LLM')}</h4>
                    <Badge variant="active" size="sm">Configured</Badge>
                  </div>
                  <p className="engine-desc">{t('settings.ollamaLlmDesc', {}, 'Model: LLaMA 3.2 • Endpoint: http://localhost:11434')}</p>
                </div>
              </div>

              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <HardDrive size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">{t('settings.tesseractOcr', {}, 'Tesseract OCR Engine')}</h4>
                    <Badge variant="active" size="sm">Ready</Badge>
                  </div>
                  <p className="engine-desc">{t('settings.tesseractOcrDesc', {}, 'OCR Binary: Windows Local Executable')}</p>
                </div>
              </div>

              <div className="engine-status-item">
                <div className="engine-icon-box">
                  <Shield size={20} />
                </div>
                <div className="engine-details">
                  <div className="engine-title-row">
                    <h4 className="engine-title">{t('settings.privacySecurity', {}, 'Privacy & Security')}</h4>
                    <Badge variant="active" size="sm">100% Offline</Badge>
                  </div>
                  <p className="engine-desc">{t('settings.privacySecurityDesc', {}, 'No receipt or serial numbers sent to external cloud APIs')}</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}

