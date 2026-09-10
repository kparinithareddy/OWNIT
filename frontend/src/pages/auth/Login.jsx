import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, LogIn, ArrowRight } from 'lucide-react';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('demo@ownit.local');
  const [password, setPassword] = useState('demo1234');

  const handleSubmit = (e) => {
    e.preventDefault();
    // Placeholder navigation for frontend demo
    navigate('/dashboard');
  };

  return (
    <div className="login-page">
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Welcome Back
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Sign in to manage your warranties and smart product lifecycle
        </p>
      </div>

      <form onSubmit={handleSubmit}>
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
          label="Password"
          type="password"
          icon={Lock}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          required
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <input type="checkbox" defaultChecked /> Remember me
          </label>
          <a href="#forgot" onClick={(e) => e.preventDefault()} style={{ fontSize: '0.8125rem' }}>
            Forgot password?
          </a>
        </div>

        <Button
          type="submit"
          variant="primary"
          icon={LogIn}
          fullWidth
          size="lg"
        >
          Sign In to Dashboard
        </Button>
      </form>

      <div style={{ marginTop: '24px', textAlign: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/signup" style={{ fontWeight: 600 }}>
            Create one now <ArrowRight size={14} style={{ display: 'inline', verticalAlign: 'middle' }} />
          </Link>
        </p>
      </div>
    </div>
  );
}
