import React from 'react';
import { CheckCircle2, AlertCircle, XCircle, HelpCircle, RefreshCw } from 'lucide-react';
import { RetrievalOutcome } from '@/lib/types';

export interface OutcomeBadgeProps {
  outcome: RetrievalOutcome;
  size?: 'sm' | 'md';
}

export const OutcomeBadge: React.FC<OutcomeBadgeProps> = ({ outcome, size = 'md' }) => {
  const normalized = (outcome || '').toLowerCase();

  const getConfig = () => {
    switch (normalized) {
      case 'found_quickly':
        return {
          label: 'Found Quickly',
          icon: <CheckCircle2 size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(16, 185, 129, 0.12)',
          text: '#10b981',
          border: 'rgba(16, 185, 129, 0.25)',
        };
      case 'found_after_effort':
        return {
          label: 'Found After Effort',
          icon: <RefreshCw size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(59, 130, 246, 0.12)',
          text: '#60a5fa',
          border: 'rgba(59, 130, 246, 0.25)',
        };
      case 'gave_up':
        return {
          label: 'Gave Up / Abandoned',
          icon: <XCircle size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(239, 68, 68, 0.12)',
          text: '#f87171',
          border: 'rgba(239, 68, 68, 0.25)',
        };
      case 'never_found':
        return {
          label: 'Never Found',
          icon: <XCircle size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(220, 38, 38, 0.15)',
          text: '#ef4444',
          border: 'rgba(220, 38, 38, 0.3)',
        };
      case 'found_alternative':
        return {
          label: 'Workaround / Alternative',
          icon: <AlertCircle size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(245, 158, 11, 0.12)',
          text: '#fbbf24',
          border: 'rgba(245, 158, 11, 0.25)',
        };
      default:
        return {
          label: outcome || 'Ambiguous',
          icon: <HelpCircle size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(255, 255, 255, 0.08)',
          text: '#9ca3af',
          border: 'rgba(255, 255, 255, 0.15)',
        };
    }
  };

  const config = getConfig();

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        background: config.bg,
        color: config.text,
        border: `1px solid ${config.border}`,
        borderRadius: 'var(--radius-full, 9999px)',
        padding: size === 'sm' ? '0.15rem 0.5rem' : '0.2rem 0.6rem',
        fontSize: size === 'sm' ? '0.7rem' : '0.75rem',
        fontWeight: 500,
        whiteSpace: 'nowrap',
      }}
    >
      {config.icon}
      <span>{config.label}</span>
    </span>
  );
};
