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
            <span style={{ color: 'var(--google-blue)', fontWeight: 600 }}>
              Google Photos Insights
            </span>
            <ChevronRight size={14} />
            <span style={{ color: 'var(--text-secondary)' }}>
              Search Complaints &amp; Feature Recommendations
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1
              style={{
                fontSize: '1.4rem',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
              }}
            >
              Google Photos Search Feedback &amp; Ideas
            </h1>
            <Badge variant="info">
              Real User Reviews
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
            Add More Reviews
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowAnalyzeModal(true)}
            leftIcon={<Sparkles size={15} />}
          >
            Analyze with AI
          </Button>
        </div>
      </div>

      {/* 9-View Navigation Bar */}
      <ProjectNav projectId={projectId} />

      {/* View Page Content */}
      <div>{children}</div>

      {/* Ingestion Dialog Modal */}
      <Modal
        isOpen={showIngestModal}
        onClose={() => setShowIngestModal(false)}
        title="Import User Reviews"
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
              Start Review Import
            </Button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem' }}>
              Choose Where to Get Reviews
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
              Import Settings (JSON)
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
        title="Analyze Reviews with AI"
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
              Start AI Analysis
            </Button>
          </>
        }
      >
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          This will use Google Gemini AI to analyze all collected user reviews:
        </p>
        <ul style={{ margin: '1rem 0 1rem 1.25rem', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          <li><strong>Step 1:</strong> Filter out unrelated comments and keep genuine search complaints.</li>
          <li><strong>Step 2:</strong> Extract the user situation, why search failed, and direct quotes.</li>
          <li><strong>Step 3:</strong> Group issues into problem themes and highlight actionable product improvements.</li>
        </ul>
      </Modal>
    </div>
  );
}
