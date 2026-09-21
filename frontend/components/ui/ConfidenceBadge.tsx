import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

export interface ConfidenceBadgeProps {
  score: number; // 0.0 - 1.0
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  score,
  showLabel = true,
  size = 'md',
}) => {
  const percent = Math.round(score * 100);

  let variant: {
    bg: string;
    text: string;
    border: string;
    icon: React.ReactNode;
    label: string;
  };

  if (score >= 0.7) {
    variant = {
      bg: 'rgba(16, 185, 129, 0.12)',
      text: '#34d399',
      border: 'rgba(16, 185, 129, 0.3)',
      icon: <ShieldCheck size={size === 'sm' ? 12 : 14} />,
      label: 'High Confidence',
    };
  } else if (score >= 0.5) {
    variant = {
      bg: 'rgba(245, 158, 11, 0.12)',
      text: '#fbbf24',
      border: 'rgba(245, 158, 11, 0.3)',
      icon: <AlertTriangle size={size === 'sm' ? 12 : 14} />,
      label: 'Needs Review',
    };
  } else {
    variant = {
      bg: 'rgba(239, 68, 68, 0.12)',
      text: '#f87171',
      border: 'rgba(239, 68, 68, 0.3)',
      icon: <ShieldAlert size={size === 'sm' ? 12 : 14} />,
      label: 'Low Confidence',
    };
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        background: variant.bg,
        color: variant.text,
        border: `1px solid ${variant.border}`,
        borderRadius: 'var(--radius-full, 9999px)',
        padding: size === 'sm' ? '0.15rem 0.5rem' : '0.25rem 0.65rem',
        fontSize: size === 'sm' ? '0.7rem' : '0.775rem',
        fontWeight: 600,
        fontFamily: 'var(--font-mono, monospace)',
      }}
      title={`Confidence Score: ${score.toFixed(2)} (${variant.label})`}
    >
      {variant.icon}
      <span>{percent}%</span>
      {showLabel && size !== 'sm' && (
        <span style={{ fontWeight: 400, opacity: 0.85, marginLeft: '0.15rem' }}>
          • {variant.label}
        </span>
      )}
    </span>
  );
};
