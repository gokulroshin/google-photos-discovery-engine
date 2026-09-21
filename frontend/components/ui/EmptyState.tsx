import React from 'react';
import { Database, Plus } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  style?: React.CSSProperties;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  style,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '3.5rem 1.5rem',
        background: 'var(--bg-surface, rgba(17, 24, 39, 0.6))',
        border: '1px dashed var(--border-subtle)',
        borderRadius: 'var(--radius-lg, 16px)',
        margin: '1.5rem 0',
        ...style,
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'rgba(66, 133, 244, 0.1)',
          color: 'var(--google-blue, #4285f4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1rem',
        }}
      >
        {icon || <Database size={28} />}
      </div>
      <h3
        style={{
          fontSize: '1.2rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
          marginBottom: '0.5rem',
        }}
      >
        {title}
      </h3>
      <p
        style={{
          color: 'var(--text-secondary)',
          fontSize: '0.925rem',
          maxWidth: '480px',
          lineHeight: 1.6,
          marginBottom: actionLabel && onAction ? '1.5rem' : '0',
        }}
      >
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction} leftIcon={<Plus size={16} />}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
