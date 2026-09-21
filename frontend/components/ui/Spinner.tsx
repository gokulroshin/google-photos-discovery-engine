import React from 'react';
import { Loader2 } from 'lucide-react';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  label?: string;
  style?: React.CSSProperties;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', label, style }) => {
  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 16;
      case 'lg':
        return 32;
      case 'xl':
        return 48;
      case 'md':
      default:
        return 24;
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        padding: '2rem',
        color: 'var(--text-secondary)',
        ...style,
      }}
    >
      <Loader2
        size={getIconSize()}
        style={{
          color: 'var(--accent-primary, #3b82f6)',
          animation: 'spin 1s linear infinite',
        }}
      />
      {label && <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{label}</div>}
    </div>
  );
};
