import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import './Input.css';

export default function Input({
  label,
  id,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  helperText,
  icon: Icon,
  required = false,
  disabled = false,
  fullWidth = true,
  className = '',
  ...rest
}) {
  const [showPassword, setShowPassword] = useState(false);
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
  const isPassword = type === 'password';
  const effectiveType = isPassword ? (showPassword ? 'text' : 'password') : type;

  return (
    <div className={`input-group ${fullWidth ? 'input-full-width' : ''} ${error ? 'input-has-error' : ''} ${className}`}>
      {label && (
        <label htmlFor={inputId} className="input-label">
          {label} {required && <span className="input-required">*</span>}
        </label>
      )}

      <div className="input-wrapper">
        {Icon && <Icon className="input-icon-left" size={18} />}
        <input
          id={inputId}
          type={effectiveType}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          className={`input-field ${Icon ? 'input-with-left-icon' : ''} ${isPassword ? 'input-with-right-icon' : ''}`}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            className="input-password-toggle"
            onClick={() => setShowPassword(!showPassword)}
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>

      {error ? (
        <p className="input-error-text">{error}</p>
      ) : helperText ? (
        <p className="input-helper-text">{helperText}</p>
      ) : null}
    </div>
  );
}

export function Select({
  label,
  id,
  options = [],
  value,
  onChange,
  error,
  helperText,
  required = false,
  disabled = false,
  fullWidth = true,
  className = '',
  ...rest
}) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`input-group ${fullWidth ? 'input-full-width' : ''} ${error ? 'input-has-error' : ''} ${className}`}>
      {label && (
        <label htmlFor={inputId} className="input-label">
          {label} {required && <span className="input-required">*</span>}
        </label>
      )}

      <div className="input-wrapper">
        <select
          id={inputId}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          className="input-field input-select"
          {...rest}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <p className="input-error-text">{error}</p>
      ) : helperText ? (
        <p className="input-helper-text">{helperText}</p>
      ) : null}
    </div>
  );
}
