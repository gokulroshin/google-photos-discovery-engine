import React, { useState } from 'react';

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children, position = 'top' }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          style={{
            position: 'absolute',
            ...(position === 'top' && { bottom: '100%', left: '50%', transform: 'translateX(-50%) translateY(-6px)' }),
            ...(position === 'bottom' && { top: '100%', left: '50%', transform: 'translateX(-50%) translateY(6px)' }),
            ...(position === 'left' && { right: '100%', top: '50%', transform: 'translateY(-50%) translateX(-6px)' }),
            ...(position === 'right' && { left: '100%', top: '50%', transform: 'translateY(-50%) translateX(6px)' }),
            background: 'var(--bg-primary, #0b0f19)',
            border: '1px solid var(--border-subtle, rgba(255,255,255,0.2))',
            color: 'var(--text-primary, #f9fafb)',
            padding: '0.4rem 0.75rem',
            borderRadius: 'var(--radius-sm, 6px)',
            fontSize: '0.75rem',
            whiteSpace: 'nowrap',
            zIndex: 100,
            boxShadow: 'var(--shadow-md)',
            pointerEvents: 'none',
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
};
