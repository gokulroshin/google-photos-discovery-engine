'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight,
  FolderGit2,
  Sparkles,
  Download,
  AlertTriangle,
  Play,
  Layers,
} from 'lucide-react';
import { api } from '@/lib/api';
import { ProjectNav } from '@/components/ProjectNav';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const projectId = params?.id as string;

  const [showIngestModal, setShowIngestModal] = useState(false);
  const [showAnalyzeModal, setShowAnalyzeModal] = useState(false);
  const [selectedSource, setSelectedSource] = useState('play_store');
  const [ingestConfig, setIngestConfig] = useState('{"app_id": "com.google.android.apps.photos", "limit": 100}');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: project, isLoading: isProjectLoading, refetch: refetchProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !!projectId,
  });

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => api.getProjectStats(projectId),
    enabled: !!projectId,
    refetchInterval: 10000,
  });

  const handleStartIngest = async () => {
    setIsSubmitting(true);
    try {
      let parsedConfig = {};
      try {
        parsedConfig = JSON.parse(ingestConfig);
      } catch {}
      await api.createJob(projectId, {
        source_type: selectedSource,
        config: parsedConfig,
      });
      setShowIngestModal(false);
      refetchStats();
    } catch (e: any) {
      alert(e.message || 'Failed to start ingestion job');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartAnalyze = async () => {
    setIsSubmitting(true);
    try {
      await api.startAnalysis(projectId);
      setShowAnalyzeModal(false);
      refetchStats();
    } catch (e: any) {
      alert(e.message || 'Failed to start analysis run');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      {/* Project Breadcrumb & Actions Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.25rem',
        }}
      >
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.85rem',
              color: 'var(--text-muted)',
              marginBottom: '0.35rem',
            }}
          >
            <Link href="/projects" style={{ color: 'var(--text-secondary)' }}>
              Projects
            </Link>
            <ChevronRight size={14} />
            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
              {project?.name || projectId}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1
              style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
              }}
            >
              {project?.name || 'Research Project'}
            </h1>
            <Badge variant={project?.status === 'active' ? 'success' : 'neutral'}>
              {project?.status || 'Active'}
            </Badge>
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowIngestModal(true)}
            leftIcon={<Download size={15} />}
          >
            Ingest Source Data
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowAnalyzeModal(true)}
            leftIcon={<Sparkles size={15} />}
          >
            Run Gemini Classification
          </Button>
        </div>
      </div>

      {/* Active System Warnings Banner */}
      {stats?.warnings?.is_partial_dataset && (
        <Alert
          variant="warning"
          title="Partial Dataset in Progress"
          style={{ marginBottom: '1.25rem' }}
        >
          Data ingestion or classification jobs are currently running. Research metrics and taxonomy reflect incomplete sample data.
        </Alert>
      )}

      {stats?.warnings?.has_pending_reviews && (
        <Alert
          variant="warning"
          title={`${stats.warnings.pending_reviews_count} Records Need Human Review`}
          style={{ marginBottom: '1.25rem' }}
          action={
            <Link href={`/projects/${projectId}/review`}>
              <Button size="sm" variant="outline" style={{ borderColor: 'rgba(245, 158, 11, 0.4)' }}>
                Open Review Queue
              </Button>
            </Link>
          }
        >
          Low confidence classification results are awaiting researcher verification to ensure research rigor.
        </Alert>
      )}

      {/* 9-View Navigation Bar */}
      <ProjectNav projectId={projectId} />

      {/* View Page Content */}
      <div>{children}</div>

      {/* Ingestion Dialog Modal */}
      <Modal
        isOpen={showIngestModal}
        onClose={() => setShowIngestModal(false)}
        title="Start Source Data Ingestion"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowIngestModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStartIngest}
              isLoading={isSubmitting}
              leftIcon={<Download size={16} />}
            >
              Start Ingestion Job
            </Button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem' }}>
              Select Source Adapter
            </label>
            <select
              value={selectedSource}
              onChange={(e) => {
                setSelectedSource(e.target.value);
                if (e.target.value === 'play_store') {
                  setIngestConfig('{"app_id": "com.google.android.apps.photos", "limit": 100}');
                } else if (e.target.value === 'reddit') {
                  setIngestConfig('{"subreddits": ["googlephotos", "Android"], "limit": 50}');
                } else if (e.target.value === 'app_store') {
                  setIngestConfig('{"app_id": "962194608", "limit": 50}');
                } else {
                  setIngestConfig('{"limit": 50}');
                }
              }}
              style={{
                width: '100%',
                padding: '0.6rem 0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="play_store">Google Play Store Reviews</option>
              <option value="app_store">Apple App Store Reviews</option>
              <option value="reddit">Reddit Public Discussions</option>
              <option value="youtube">YouTube Commentary</option>
              <option value="forum">Google Photos Support Forum</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem' }}>
              Adapter Configuration (JSON)
            </label>
            <textarea
              value={ingestConfig}
              onChange={(e) => setIngestConfig(e.target.value)}
              rows={4}
              style={{
                width: '100%',
                padding: '0.6rem 0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
              }}
            />
          </div>
        </div>
      </Modal>

      {/* Analyze Dialog Modal */}
      <Modal
        isOpen={showAnalyzeModal}
        onClose={() => setShowAnalyzeModal(false)}
        title="Trigger Gemini AI Classification Run"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowAnalyzeModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStartAnalyze}
              isLoading={isSubmitting}
              leftIcon={<Sparkles size={16} />}
            >
              Launch Analysis Worker
            </Button>
          </>
        }
      >
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          This will trigger a 2-stage Gemini extraction worker across all unanalyzed source records:
        </p>
        <ul style={{ margin: '1rem 0 1rem 1.25rem', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          <li><strong>Stage 1:</strong> Relevance gating and genuine user experience classification.</li>
          <li><strong>Stage 2:</strong> 12-field structured extraction (memory cues, scenario, failure points, outcome, verbatim excerpt).</li>
          <li><strong>Stage 3:</strong> 768-d vector embedding generation and human review tagging for confidence &lt; 0.70.</li>
        </ul>
      </Modal>
    </div>
  );
}
