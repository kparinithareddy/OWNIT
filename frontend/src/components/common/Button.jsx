import React from 'react';
import { Loader2 } from 'lucide-react';
import './Button.css';

export default function Button({
  children,
  variant = 'primary', // 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size = 'md',        // 'xs' | 'sm' | 'md' | 'lg'
  icon: Icon,
  iconPosition = 'left',
  fullWidth = false,
  disabled = false,
  loading = false,
  className = '',
  onClick,
  type = 'button',
  ...rest
}) {
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth ? 'btn-full-width' : '',
    loading ? 'btn-loading' : '',
    className
  ].filter(Boolean).join(' ');

  const iconSize = size === 'xs' ? 12 : size === 'sm' ? 14 : size === 'lg' ? 18 : 16;

  const renderIcon = (IconItem) => {
    if (!IconItem) return null;
    if (React.isValidElement(IconItem)) {
      return IconItem;
    }
    const Comp = IconItem;
    return <Comp className="btn-icon" size={iconSize} />;
  };

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading}
      onClick={onClick}
      {...rest}
    >
      {loading ? (
        <Loader2 className="btn-icon btn-spinner spinning" size={iconSize} />
      ) : (
        Icon && iconPosition === 'left' && renderIcon(Icon)
      )}
      {children && <span className="btn-text">{children}</span>}
      {!loading && Icon && iconPosition === 'right' && renderIcon(Icon)}
    </button>
  );
}
