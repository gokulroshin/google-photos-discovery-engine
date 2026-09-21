import React from 'react';
import { Smartphone, Apple, MessageSquare, Youtube, MessagesSquare, UploadCloud, Globe } from 'lucide-react';
import { Platform } from '@/lib/types';

export interface SourceBadgeProps {
  platform: Platform | string;
  size?: 'sm' | 'md';
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ platform, size = 'md' }) => {
  const normalized = (platform || '').toLowerCase().replace('-', '_');

  const getConfig = () => {
    switch (normalized) {
      case 'play_store':
      case 'google_play':
        return {
          label: 'Google Play',
          icon: <Smartphone size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(52, 168, 83, 0.12)',
          text: '#34a853',
          border: 'rgba(52, 168, 83, 0.25)',
        };
      case 'app_store':
        return {
          label: 'App Store',
          icon: <Apple size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(59, 130, 246, 0.12)',
          text: '#60a5fa',
          border: 'rgba(59, 130, 246, 0.25)',
        };
      case 'reddit':
        return {
          label: 'Reddit',
          icon: <MessageSquare size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(255, 69, 0, 0.12)',
          text: '#ff6433',
          border: 'rgba(255, 69, 0, 0.25)',
        };
      case 'youtube':
        return {
          label: 'YouTube',
          icon: <Youtube size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(234, 67, 53, 0.12)',
          text: '#ea4335',
          border: 'rgba(234, 67, 53, 0.25)',
        };
      case 'support_forum':
      case 'forum':
        return {
          label: 'Support Forum',
          icon: <MessagesSquare size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(251, 188, 5, 0.12)',
          text: '#fbbc05',
          border: 'rgba(251, 188, 5, 0.25)',
        };
      case 'manual_upload':
      case 'manual_import':
        return {
          label: 'Manual Import',
          icon: <UploadCloud size={size === 'sm' ? 12 : 14} />,
          bg: 'rgba(139, 92, 246, 0.12)',
          text: '#a78bfa',
          border: 'rgba(139, 92, 246, 0.25)',
        };
      default:
        return {
          label: platform || 'Web Source',
          icon: <Globe size={size === 'sm' ? 12 : 14} />,
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
