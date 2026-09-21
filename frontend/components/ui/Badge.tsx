import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'info' | 'success' | 'warning' | 'danger' | 'neutral' | 'purple';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  style,
  className = '',
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'info':
        return {
          background: 'rgba(66, 133, 244, 0.12)',
          color: '#60a5fa',
          borderColor: 'rgba(66, 133, 244, 0.25)',
        };
      case 'success':
        return {
          background: 'rgba(16, 185, 129, 0.12)',
          color: '#34d399',
          borderColor: 'rgba(16, 185, 129, 0.25)',
        };
      case 'warning':
        return {
          background: 'rgba(245, 158, 11, 0.12)',
          color: '#fbbf24',
          borderColor: 'rgba(245, 158, 11, 0.25)',
        };
      case 'danger':
        return {
          background: 'rgba(239, 68, 68, 0.12)',
          color: '#f87171',
          borderColor: 'rgba(239, 68, 68, 0.25)',
        };
      case 'purple':
        return {
          background: 'rgba(139, 92, 246, 0.12)',
          color: '#a78bfa',
          borderColor: 'rgba(139, 92, 246, 0.25)',
        };
      case 'neutral':
      default:
        return {
          background: 'rgba(255, 255, 255, 0.06)',
          color: '#9ca3af',
          borderColor: 'rgba(255, 255, 255, 0.1)',
        };
    }
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        fontWeight: 500,
        borderRadius: 'var(--radius-full, 9999px)',
        borderWidth: '1px',
        borderStyle: 'solid',
        padding: size === 'sm' ? '0.15rem 0.5rem' : '0.25rem 0.65rem',
        fontSize: size === 'sm' ? '0.7rem' : '0.775rem',
        lineHeight: 1.2,
        ...getVariantStyles(),
        ...style,
      }}
      className={className}
      {...props}
    >
      {children}
    </span>
  );
};
