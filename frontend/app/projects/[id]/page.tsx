'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Sparkles,
  Layers,
  BarChart3,
  ShieldAlert,
  ArrowRight,
  Activity,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Play,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Cell,
} from 'recharts';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';

const PLATFORM_COLORS: Record<string, string> = {
  play_store: '#34a853',
  google_play: '#34a853',
  reddit: '#ff6433',
  app_store: '#4285f4',
  forum: '#fbbc05',
  support_forum: '#fbbc05',
  youtube: '#ea4335',
  manual_import: '#8b5cf6',
  manual_upload: '#8b5cf6',
};

const CONFIDENCE_COLORS: Record<string, string> = {
  '0.0-0.5 (Low)': '#ef4444',
  '0.5-0.7 (Moderate)': '#f59e0b',
  '0.7-0.85 (High)': '#3b82f6',
  '0.85-1.0 (Very High)': '#10b981',
};

export default function ProjectOverviewPage() {
  const params = useParams();
  const projectId = params?.id as string;

  const { data: project, isLoading: isProjectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !!projectId,
  });

  const { data: stats, isLoading: isStatsLoading } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => api.getProjectStats(projectId),
    enabled: !!projectId,
    refetchInterval: 10000,
  });

  if (isProjectLoading || isStatsLoading) {
    return <Spinner size="lg" label="Loading project overview..." style={{ minHeight: '300px' }} />;
  }

  const totalRecords = stats?.total_records || 0;
  const totalEvidence = stats?.total_evidence || 0;
  const reviewQueueDepth = stats?.review_queue_depth || 0;
  const categoriesCount = stats?.categories_count || 0;
  const opportunitiesCount = stats?.opportunities_count || 0;

  if (totalRecords === 0) {
    return (
      <EmptyState
        title="No Source Records Collected Yet"
        description="To begin uncovering retrieval failure modes, trigger an automated source adapter (Google Play, Reddit, App Store) or import a CSV/JSON dataset."
        actionLabel="Start First Ingestion Job"
        onAction={() => {
          // Open jobs tab
          window.location.href = `/projects/${projectId}/jobs`;
        }}
      />
    );
  }

  // Transform source diversity for recharts
  const sourceChartData = Object.entries(stats?.source_diversity || {}).map(([platform, count]) => ({
    name: platform.replace('_', ' ').toUpperCase(),
    rawKey: platform,
    count,
  }));

  // Transform confidence distribution for recharts
  const confidenceChartData = Object.entries(stats?.confidence_distribution || {}).map(([range, count]) => ({
    range,
    count,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* 5 Core Metric Summary Cards */}
      <div className="grid-5" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(66, 133, 244, 0.15)', color: 'var(--google-blue)' }}>
              <Database size={18} />
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Raw Source Records</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {totalRecords.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Across {Object.keys(stats?.source_diversity || {}).length} platforms
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--status-success)' }}>
              <Sparkles size={18} />
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Relevant Evidence</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {totalEvidence.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            {totalRecords > 0 ? `${Math.round((totalEvidence / totalRecords) * 100)}% relevance yield` : '0%'}
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(139, 92, 246, 0.15)', color: '#a78bfa' }}>
              <Layers size={18} />
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Taxonomy Categories</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {categoriesCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Failure clusters
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(236, 72, 153, 0.15)', color: '#ec4899' }}>
              <BarChart3 size={18} />
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Opportunity Areas</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {opportunitiesCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Scored on 9 dimensions
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem', border: reviewQueueDepth > 0 ? '1px solid rgba(245, 158, 11, 0.3)' : undefined }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--status-warning)' }}>
              <ShieldAlert size={18} />
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Review Queue</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: reviewQueueDepth > 0 ? 'var(--status-warning)' : 'var(--text-primary)' }}>
            {reviewQueueDepth}
          </div>
          <Link
            href={`/projects/${projectId}/review`}
            style={{
              fontSize: '0.75rem',
              color: 'var(--google-blue)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              marginTop: '0.25rem',
            }}
          >
            Review records <ArrowRight size={12} />
          </Link>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Source Diversity Chart */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Source Diversity Breakdown</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Distribution of raw records across public channels
              </p>
            </div>
            <Badge variant="info">Multi-Platform</Badge>
          </div>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#6b7280" fontSize={11} tickLine={false} />
                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} />
                <RechartsTooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {sourceChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PLATFORM_COLORS[entry.rawKey] || '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confidence Distribution Histogram */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Confidence Distribution</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Gemini classification certainty across evidence records
              </p>
            </div>
            <Badge variant="purple">Gemini 1.5 Pro</Badge>
          </div>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confidenceChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="range" stroke="#6b7280" fontSize={10} tickLine={false} />
                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} />
                <RechartsTooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {confidenceChartData.map((entry, index) => (
                    <Cell key={`cell-conf-${index}`} fill={CONFIDENCE_COLORS[entry.range] || '#8b5cf6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Job Activity Strip */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Recent Pipeline Activity</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Execution status of recent data ingestion and classification runs
            </p>
          </div>
          <Link href={`/projects/${projectId}/jobs`}>
            <Button size="sm" variant="outline" rightIcon={<ArrowRight size={14} />}>
              View All Jobs
            </Button>
          </Link>
        </div>

        {stats?.recent_jobs && stats.recent_jobs.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {stats.recent_jobs.map((job) => (
              <div
                key={job.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.85rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ color: job.status === 'completed' ? '#10b981' : job.status === 'running' ? '#3b82f6' : '#ef4444' }}>
                    {job.status === 'completed' ? <CheckCircle2 size={16} /> : <Activity size={16} />}
                  </div>
                  <div>
                    <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {job.job_type} ({job.source_type})
                    </span>
                    <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem', fontSize: '0.75rem' }}>
                      ID: {job.id.substring(0, 12)}...
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    <strong>{job.records_stored}</strong> stored / <strong>{job.records_found}</strong> found
                  </span>
                  <Badge variant={job.status === 'completed' ? 'success' : job.status === 'running' ? 'info' : 'danger'}>
                    {job.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
            No recent job activity recorded.
          </div>
        )}
      </div>
    </div>
  );
}
