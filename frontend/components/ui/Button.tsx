import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'success';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  className = '',
  style,
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'primary':
        return {
          background: 'var(--accent-gradient, linear-gradient(135deg, #4285f4 0%, #8b5cf6 100%))',
          color: '#ffffff',
          border: 'none',
          boxShadow: '0 2px 8px rgba(66, 133, 244, 0.3)',
        };
      case 'danger':
        return {
          background: 'rgba(239, 68, 68, 0.15)',
          color: '#ef4444',
          border: '1px solid rgba(239, 68, 68, 0.3)',
        };
      case 'success':
        return {
          background: 'rgba(16, 185, 129, 0.15)',
          color: '#10b981',
          border: '1px solid rgba(16, 185, 129, 0.3)',
        };
      case 'outline':
        return {
          background: 'transparent',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-subtle)',
        };
      case 'ghost':
        return {
          background: 'transparent',
          color: 'var(--text-secondary)',
          border: 'none',
        };
      case 'secondary':
      default:
        return {
          background: 'var(--bg-tertiary)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-subtle)',
        };
    }
  };

  const getSizeStyles = (): React.CSSProperties => {
    switch (size) {
      case 'sm':
        return {
          padding: '0.35rem 0.75rem',
          fontSize: '0.8125rem',
          gap: '0.35rem',
        };
      case 'lg':
        return {
          padding: '0.75rem 1.5rem',
          fontSize: '1rem',
          gap: '0.6rem',
        };
      case 'md':
      default:
        return {
          padding: '0.5rem 1.1rem',
          fontSize: '0.875rem',
          gap: '0.5rem',
        };
    }
  };

  return (
    <button
      disabled={disabled || isLoading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 500,
        borderRadius: 'var(--radius-md, 8px)',
        cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
        opacity: disabled || isLoading ? 0.6 : 1,
        transition: 'all var(--transition-fast, 0.15s ease)',
        whiteSpace: 'nowrap',
        outline: 'none',
        ...getVariantStyles(),
        ...getSizeStyles(),
        ...style,
      }}
      className={className}
      {...props}
    >
      {isLoading ? (
        <Loader2 size={size === 'sm' ? 14 : 18} style={{ animation: 'spin 1s linear infinite' }} />
      ) : (
        leftIcon
      )}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};
