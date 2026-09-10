import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Lock, UserPlus, ArrowLeft, AlertCircle } from 'lucide-react';
import Input, { Select } from '../../components/common/Input';
import Button from '../../components/common/Button';
import { useAuth } from '../../context/AuthContext';
import { ApiError } from '../../services/api';

export default function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('en');
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
      setErrorMessage('Username is required.');
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
      navigate('/dashboard', { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('An unexpected error occurred during signup. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="signup-page">
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Create Your Account
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Start taking control of all your warranties and product lifecycles
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
          label="Username"
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
          label="Password"
          type="password"
          icon={Lock}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          required
          disabled={isSubmitting}
        />

        <Input
          label="Confirm Password"
          type="password"
          icon={Lock}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Re-enter your password"
          required
          disabled={isSubmitting}
        />

        <Select
          label="Preferred Language"
          options={languageOptions}
          value={preferredLanguage}
          onChange={(e) => setPreferredLanguage(e.target.value)}
          helperText="We support English, Hindi, and Telugu."
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
          {isSubmitting ? 'Creating Account...' : 'Create Account'}
        </Button>
      </form>

      <div style={{ marginTop: '24px', textAlign: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ fontWeight: 600 }}>
            <ArrowLeft size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
