import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, UserPlus, ArrowLeft } from 'lucide-react';
import Input, { Select } from '../../components/common/Input';
import Button from '../../components/common/Button';

export default function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e) => {
    e.preventDefault();
    // Placeholder navigation for frontend demo
    navigate('/dashboard');
  };

  const languageOptions = [
    { value: 'en', label: 'English (Default)' },
    { value: 'hi', label: 'हिंदी (Hindi)' },
    { value: 'te', label: 'తెలుగు (Telugu)' }
  ];

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

      <form onSubmit={handleSubmit}>
        <Input
          label="Full Name"
          type="text"
          icon={User}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Parinitha Reddy"
          required
        />

        <Input
          label="Email Address"
          type="email"
          icon={Mail}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="your.email@example.com"
          required
        />

        <Input
          label="Create Password"
          type="password"
          icon={Lock}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          helperText="Must include letters & numbers"
          required
        />

        <Select
          label="Preferred Language"
          options={languageOptions}
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          helperText="We support English, Hindi, and Telugu."
        />

        <Button
          type="submit"
          variant="primary"
          icon={UserPlus}
          fullWidth
          size="lg"
        >
          Create Free Account
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
