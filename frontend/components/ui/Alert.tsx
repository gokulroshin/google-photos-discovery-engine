import React from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, X } from 'lucide-react';

export interface AlertProps {
  variant?: 'warning' | 'danger' | 'info' | 'success';
  title?: string;
  children: React.ReactNode;
  onDismiss?: () => void;
  action?: React.ReactNode;
  style?: React.CSSProperties;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'warning',
  title,
  children,
  onDismiss,
  action,
  style,
}) => {
  const getStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          bg: 'rgba(239, 68, 68, 0.1)',
          border: 'rgba(239, 68, 68, 0.3)',
          text: '#f87171',
          icon: <AlertCircle size={18} color="#ef4444" />,
        };
      case 'info':
        return {
          bg: 'rgba(59, 130, 246, 0.1)',
          border: 'rgba(59, 130, 246, 0.3)',
          text: '#93c5fd',
          icon: <Info size={18} color="#3b82f6" />,
        };
      case 'success':
        return {
          bg: 'rgba(16, 185, 129, 0.1)',
          border: 'rgba(16, 185, 129, 0.3)',
          text: '#6ee7b7',
          icon: <CheckCircle2 size={18} color="#10b981" />,
        };
      case 'warning':
      default:
        return {
          bg: 'rgba(245, 158, 11, 0.1)',
          border: 'rgba(245, 158, 11, 0.3)',
          text: '#fcd34d',
          icon: <AlertTriangle size={18} color="#f59e0b" />,
        };
    }
  };

  const current = getStyles();

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.85rem',
        padding: '0.85rem 1.15rem',
        borderRadius: 'var(--radius-md, 8px)',
        background: current.bg,
        border: `1px solid ${current.border}`,
        color: current.text,
        fontSize: '0.875rem',
        lineHeight: 1.5,
        ...style,
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>{current.icon}</div>
      <div style={{ flex: 1 }}>
        {title && (
          <div style={{ fontWeight: 600, marginBottom: '0.2rem', color: '#ffffff' }}>
            {title}
          </div>
        )}
        <div style={{ opacity: 0.95 }}>{children}</div>
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            opacity: 0.6,
            cursor: 'pointer',
            padding: '2px',
          }}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};
