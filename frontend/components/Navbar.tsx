'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Sparkles,
  Layers,
  Search,
  CheckCircle2,
  AlertCircle,
  Database,
  BarChart3,
  FileText,
  UserCheck,
  Activity,
  LogOut,
  FolderGit2
} from 'lucide-react';
import { useAuthStore } from '@/lib/auth-store';
import { api } from '@/lib/api';
import { HealthStatus } from '@/lib/types';

export function Navbar() {
  const pathname = usePathname();
  const { user, logout, activeProjectId } = useAuthStore();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getHealth().then((res) => {
      if (isMounted) setHealth(res);
    });
    const interval = setInterval(() => {
      api.getHealth().then((res) => {
        if (isMounted) setHealth(res);
      });
    }, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const isAuthPage = pathname?.includes('/login');
  if (isAuthPage) return null;

  const currentProjectId = activeProjectId || 'proj_photo_retrieval_2026';

  return (
    <header className="navbar">
      <div className="nav-brand">
        <Link href="/projects" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="brand-icon-wrapper">
            <Sparkles size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>Photos Discovery</span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                AI Core
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>
              Retrieval Failure Intelligence
            </div>
          </div>
        </Link>
      </div>

      <nav className="nav-links">
        <Link
          href="/projects"
          className={`nav-link ${pathname === '/projects' ? 'active' : ''}`}
        >
          <FolderGit2 size={16} />
          <span>Projects</span>
        </Link>
        <Link
          href={`/projects/${currentProjectId}`}
          className={`nav-link ${pathname === `/projects/${currentProjectId}` ? 'active' : ''}`}
        >
          <BarChart3 size={16} />
          <span>Overview</span>
        </Link>
        <Link
          href={`/projects/${currentProjectId}/explorer`}
          className={`nav-link ${pathname?.includes('/explorer') ? 'active' : ''}`}
        >
          <Database size={16} />
          <span>Explorer</span>
        </Link>
        <Link
          href={`/projects/${currentProjectId}/evidence`}
          className={`nav-link ${pathname?.includes('/evidence') ? 'active' : ''}`}
        >
          <Search size={16} />
          <span>Evidence</span>
        </Link>
        <Link
          href={`/projects/${currentProjectId}/taxonomy`}
          className={`nav-link ${pathname?.includes('/taxonomy') ? 'active' : ''}`}
        >
          <Layers size={16} />
          <span>Taxonomy</span>
        </Link>
        <Link
          href={`/projects/${currentProjectId}/review`}
          className={`nav-link ${pathname?.includes('/review') ? 'active' : ''}`}
        >
          <UserCheck size={16} />
          <span>Review</span>
        </Link>
        <Link
          href={`/projects/${currentProjectId}/jobs`}
          className={`nav-link ${pathname?.includes('/jobs') ? 'active' : ''}`}
        >
          <Activity size={16} />
          <span>Jobs</span>
        </Link>
      </nav>

      <div className="nav-actions">
        {/* Live Backend Health Indicator */}
        <div
          title={`Backend: ${health?.status || 'checking'} | DB: ${health?.database || 'unknown'} | Gemini: ${health?.gemini || 'unknown'}`}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}
        >
          {health?.status === 'ok' ? (
            <span className="badge badge-success" style={{ padding: '0.2rem 0.5rem' }}>
              <CheckCircle2 size={12} /> Live API
            </span>
          ) : (
            <span className="badge badge-warning" style={{ padding: '0.2rem 0.5rem' }}>
              <AlertCircle size={12} /> {health?.gemini === 'mock_mode' ? 'Mock Mode' : 'Connecting'}
            </span>
          )}
        </div>

        {/* Public Access Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ textAlign: 'right', fontSize: '0.8rem' }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{user?.name || 'Public Access'}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Open Research Console</div>
          </div>
          <span className="badge badge-info" style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}>
            Public
          </span>
        </div>
      </div>
    </header>
  );
}
