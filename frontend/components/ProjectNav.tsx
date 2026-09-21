'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Database,
  Sparkles,
  Layers,
  BarChart3,
  Search,
  FileText,
  CheckSquare,
  Activity,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface ProjectNavProps {
  projectId: string;
}

export const ProjectNav: React.FC<ProjectNavProps> = ({ projectId }) => {
  const pathname = usePathname();

  const { data: stats } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => api.getProjectStats(projectId),
    refetchInterval: 15000,
  });

  const navItems = [
    {
      label: 'Overview',
      href: `/projects/${projectId}`,
      icon: <LayoutDashboard size={16} />,
      exact: true,
    },
    {
      label: 'Data Explorer',
      href: `/projects/${projectId}/explorer`,
      icon: <Database size={16} />,
      badge: stats?.total_records ? `${stats.total_records}` : undefined,
    },
    {
      label: 'Evidence Viewer',
      href: `/projects/${projectId}/evidence`,
      icon: <Sparkles size={16} />,
      badge: stats?.total_evidence ? `${stats.total_evidence}` : undefined,
    },
    {
      label: 'Problem Taxonomy',
      href: `/projects/${projectId}/taxonomy`,
      icon: <Layers size={16} />,
      badge: stats?.categories_count ? `${stats.categories_count}` : undefined,
    },
    {
      label: 'Opportunities',
      href: `/projects/${projectId}/opportunities`,
      icon: <BarChart3 size={16} />,
      badge: stats?.opportunities_count ? `${stats.opportunities_count}` : undefined,
    },
    {
      label: 'Semantic Search',
      href: `/projects/${projectId}/search`,
      icon: <Search size={16} />,
    },
    {
      label: 'Research Report',
      href: `/projects/${projectId}/report`,
      icon: <FileText size={16} />,
    },
    {
      label: 'Review Queue',
      href: `/projects/${projectId}/review`,
      icon: <CheckSquare size={16} />,
      badge: stats?.review_queue_depth && stats.review_queue_depth > 0 ? `${stats.review_queue_depth}` : undefined,
      badgeVariant: 'warning',
    },
    {
      label: 'Job Monitor',
      href: `/projects/${projectId}/jobs`,
      icon: <Activity size={16} />,
    },
  ];

  const isActive = (href: string, exact: boolean = false) => {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  };

  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.4rem',
        overflowX: 'auto',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '0.75rem',
        marginBottom: '1.75rem',
        scrollbarWidth: 'none',
      }}
    >
      {navItems.map((item) => {
        const active = isActive(item.href, item.exact);
        return (
          <Link
            key={item.href}
            href={item.href}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.55rem 0.9rem',
              borderRadius: 'var(--radius-md, 8px)',
              fontSize: '0.85rem',
              fontWeight: active ? 600 : 500,
              color: active ? '#ffffff' : 'var(--text-secondary)',
              background: active ? 'var(--bg-surface-elevated, #1a2234)' : 'transparent',
              border: active ? '1px solid var(--border-focus, #3b82f6)' : '1px solid transparent',
              whiteSpace: 'nowrap',
              transition: 'all var(--transition-fast)',
              boxShadow: active ? '0 2px 8px rgba(0,0,0,0.2)' : 'none',
            }}
          >
            <span style={{ color: active ? 'var(--accent-primary, #3b82f6)' : 'inherit' }}>
              {item.icon}
            </span>
            <span>{item.label}</span>
            {item.badge && (
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  padding: '0.1rem 0.4rem',
                  borderRadius: '9999px',
                  background:
                    item.badgeVariant === 'warning'
                      ? 'rgba(245, 158, 11, 0.2)'
                      : active
                      ? 'rgba(66, 133, 244, 0.2)'
                      : 'rgba(255, 255, 255, 0.08)',
                  color:
                    item.badgeVariant === 'warning'
                      ? '#fbbf24'
                      : active
                      ? '#60a5fa'
                      : 'var(--text-muted)',
                }}
              >
                {item.badge}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
};
