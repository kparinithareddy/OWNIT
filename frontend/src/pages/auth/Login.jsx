import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { User, Lock, LogIn, ArrowRight, AlertCircle, Globe } from 'lucide-react';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { useAuth } from '../../context/AuthContext';
import { useLanguage, SUPPORTED_LANGUAGES } from '../../i18n/LanguageContext';
import { ApiError } from '../../services/api';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const { language, changeLanguage, t } = useLanguage();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!username.trim() || !password) {
      setErrorMessage(t('auth.noAccount') || 'Please enter both username and password.');
      return;
    }

    try {
      setIsSubmitting(true);
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(t('common.error') || 'An unexpected error occurred during login. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      {/* Language Toggle in Auth Card */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem' }}>
          <Globe size={14} style={{ color: 'var(--text-muted)' }} />
          {SUPPORTED_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => changeLanguage(lang.code)}
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
          {t('auth.loginTitle', {}, 'Welcome Back')}
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          {t('auth.loginSubtitle', {}, 'Sign in to access your product assets, warranties & AI assistant')}
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
          required
          disabled={isSubmitting}
        />

        <Input
          label={t('auth.password', {}, 'Password')}
          type="password"
          icon={Lock}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          required
          disabled={isSubmitting}
        />

        <Button
          type="submit"
          variant="primary"
          icon={LogIn}
          fullWidth
          size="lg"
          disabled={isSubmitting}
        >
          {isSubmitting ? t('common.loading', {}, 'Signing In...') : t('auth.signInBtn', {}, 'Sign In to OWNIT')}
        </Button>
      </form>

      <div style={{ marginTop: '24px', textAlign: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {t('auth.noAccount', {}, "Don't have an account?")}{' '}
          <Link to="/signup" style={{ fontWeight: 600 }}>
            {t('auth.signUpBtn', {}, 'Create one now')} <ArrowRight size={14} style={{ display: 'inline', verticalAlign: 'middle' }} />
          </Link>
        </p>
      </div>
    </div>
  );
}
