import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Lock, UserPlus, ArrowLeft, AlertCircle, Globe } from 'lucide-react';
import Input, { Select } from '../../components/common/Input';
import Button from '../../components/common/Button';
import { useAuth } from '../../context/AuthContext';
import { useLanguage, SUPPORTED_LANGUAGES } from '../../i18n/LanguageContext';
import { ApiError } from '../../services/api';

export default function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const { language, changeLanguage, t } = useLanguage();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState(language);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const languageOptions = [
    { value: 'en', label: 'English (Default)' },
    { value: 'hi', label: 'हिंदी (Hindi)' },
    { value: 'te', label: 'తెలుగు (Telugu)' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    const cleanUsername = username.trim();
    if (!cleanUsername) {
      setErrorMessage(t('auth.username') + ' is required.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please verify your confirmation password.');
      return;
    }

    try {
      setIsSubmitting(true);
      await signup(cleanUsername, password, confirmPassword, preferredLanguage);
      changeLanguage(preferredLanguage);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(t('common.error') || 'An unexpected error occurred during signup. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="signup-page">
      {/* Language Toggle in Auth Card */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem' }}>
          <Globe size={14} style={{ color: 'var(--text-muted)' }} />
          {SUPPORTED_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => {
                changeLanguage(lang.code);
                setPreferredLanguage(lang.code);
              }}
              style={{
                background: language === lang.code ? 'var(--primary)' : 'transparent',
                color: language === lang.code ? '#ffffff' : 'var(--text-muted)',
                border: '1px solid var(--border-color)',
                borderRadius: '4px',
                padding: '2px 8px',
                fontSize: '0.75rem',
                cursor: 'pointer',
                fontWeight: language === lang.code ? 600 : 400
              }}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
          {t('auth.signupTitle', {}, 'Create Your Account')}
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          {t('auth.signupSubtitle', {}, 'Start taking control of all your warranties and product lifecycles')}
        </p>
      </div>

      {errorMessage && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 14px',
          backgroundColor: 'var(--danger-light)',
          color: 'var(--danger)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.8125rem',
          marginBottom: '16px'
        }}>
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <Input
          label={t('auth.username', {}, 'Username')}
          type="text"
          icon={User}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="e.g. parinitha_reddy"
          helperText="3-30 characters (letters, numbers, underscores)"
          required
          disabled={isSubmitting}
        />

        <Input
          label={t('auth.password', {}, 'Password')}
          type="password"
          icon={Lock}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          required
          disabled={isSubmitting}
        />

        <Input
          label={t('auth.confirmPassword', {}, 'Confirm Password')}
          type="password"
          icon={Lock}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Re-enter your password"
          required
          disabled={isSubmitting}
        />

        <Select
          label={t('auth.preferredLanguage', {}, 'Interface Language')}
          options={languageOptions}
          value={preferredLanguage}
          onChange={(e) => {
            setPreferredLanguage(e.target.value);
            changeLanguage(e.target.value);
          }}
          helperText={t('settings.interfaceLanguageDesc', {}, 'Select English, Hindi, or Telugu.')}
          disabled={isSubmitting}
        />

        <Button
          type="submit"
          variant="primary"
          icon={UserPlus}
          fullWidth
          size="lg"
          disabled={isSubmitting}
        >
          {isSubmitting ? t('common.loading', {}, 'Creating Account...') : t('auth.signUpBtn', {}, 'Create Account')}
        </Button>
      </form>

      <div style={{ marginTop: '24px', textAlign: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {t('auth.haveAccount', {}, 'Already have an account?')}{' '}
          <Link to="/login" style={{ fontWeight: 600 }}>
            <ArrowLeft size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> {t('auth.signInBtn', {}, 'Sign In')}
          </Link>
        </p>
      </div>
    </div>
  );
}
