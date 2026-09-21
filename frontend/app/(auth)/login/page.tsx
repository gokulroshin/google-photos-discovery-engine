'use client';

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Sparkles, ShieldCheck, UserCheck, ArrowRight, Lock, Mail } from 'lucide-react';
import { useAuthStore } from '@/lib/auth-store';
import { api } from '@/lib/api';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTarget = searchParams.get('redirect') || '/projects';
  const setUser = useAuthStore((state) => state.setUser);
  const [email, setEmail] = useState('pm-research@google-photos.internal');
  const [password, setPassword] = useState('••••••••••••');
  const [role, setRole] = useState<'admin' | 'researcher'>('admin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email, role);
      setUser(res.user, res.access_token);
      router.push(redirectTarget.startsWith('/') ? redirectTarget : `/${redirectTarget}`);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setPresetRole = (selectedRole: 'admin' | 'researcher') => {
    setRole(selectedRole);
    if (selectedRole === 'admin') {
      setEmail('pm-lead@google-photos.internal');
    } else {
      setEmail('researcher@google-photos.internal');
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 4rem)',
        padding: '1rem',
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '2.5rem',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            className="brand-icon-wrapper"
            style={{ width: '48px', height: '48px', margin: '0 auto 1rem auto' }}
          >
            <Sparkles size={26} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.35rem' }}>
            Photo Retrieval Discovery
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            AI-Powered Failure Mode & Opportunity Discovery Platform
          </p>
        </div>

        {error && (
          <div
            className="badge badge-danger"
            style={{ width: '100%', padding: '0.6rem', marginBottom: '1.25rem', justifyContent: 'center' }}
          >
            {error}
          </div>
        )}

        {/* Role Presets */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Select Demo Account Role:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setPresetRole('admin')}
              className={`btn ${role === 'admin' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
              style={{ justifyContent: 'flex-start', padding: '0.5rem 0.75rem' }}
            >
              <ShieldCheck size={16} />
              <span>Admin (PM Lead)</span>
            </button>
            <button
              type="button"
              onClick={() => setPresetRole('researcher')}
              className={`btn ${role === 'researcher' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
              style={{ justifyContent: 'flex-start', padding: '0.5rem 0.75rem' }}
            >
              <UserCheck size={16} />
              <span>Researcher</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label className="input-label" htmlFor="email">
              Internal Corporate Email
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="email"
                type="email"
                className="input-field"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{ paddingLeft: '2.5rem' }}
              />
              <Mail
                size={16}
                style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                type="password"
                className="input-field"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ paddingLeft: '2.5rem' }}
              />
              <Lock
                size={16}
                style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1rem', padding: '0.8rem' }}
            disabled={loading}
          >
            <span>{loading ? 'Authenticating...' : 'Access Discovery Console'}</span>
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Strictly for Google Photos Core Experience Team research.
          <br />
          Ground truth evidence-first engine.
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="container" style={{ padding: '4rem', textAlign: 'center' }}>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}
