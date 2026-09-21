'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  Plus,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Sparkles,
  Download,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { api } from '@/lib/api';
import { IngestionJob, ModelRun } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';

export default function JobMonitoringPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'ingestion' | 'analysis'>('ingestion');
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [showAnalyzeModal, setShowAnalyzeModal] = useState(false);
  const [cancellingJobId, setCancellingJobId] = useState<string | null>(null);
  const [expandedErrorJobs, setExpandedErrorJobs] = useState<Record<string, boolean>>({});

  // Ingestion form state
  const [selectedSource, setSelectedSource] = useState('play_store');
  const [ingestConfig, setIngestConfig] = useState('{"app_id": "com.google.android.apps.photos", "limit": 100}');

  // Ingestion Jobs Query with 5s live polling
  const { data: jobsData, isLoading: isJobsLoading } = useQuery({
    queryKey: ['ingestion-jobs', projectId],
    queryFn: () => api.getJobs(projectId, { page: 1, page_size: 50 }),
    enabled: !!projectId,
    refetchInterval: 5000,
  });

  // Model Runs Query with 5s live polling
  const { data: runsData, isLoading: isRunsLoading } = useQuery({
    queryKey: ['model-runs', projectId],
    queryFn: () => api.getModelRuns(projectId, { page: 1, page_size: 50 }),
    enabled: !!projectId,
    refetchInterval: 5000,
  });

  const createJobMutation = useMutation({
    mutationFn: () => {
      let parsed = {};
      try {
        parsed = JSON.parse(ingestConfig);
      } catch {}
      return api.createJob(projectId, { source_type: selectedSource, config: parsed });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingestion-jobs', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      setShowIngestModal(false);
    },
  });

  const startAnalysisMutation = useMutation({
    mutationFn: () => api.startAnalysis(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-runs', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      setShowAnalyzeModal(false);
    },
  });

  const cancelJobMutation = useMutation({
    mutationFn: (jobId: string) => api.cancelJob(projectId, jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingestion-jobs', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      setCancellingJobId(null);
    },
  });

  const resumeRunMutation = useMutation({
    mutationFn: (runId: string) => api.resumeModelRun(projectId, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-runs', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
    },
  });

  const toggleError = (id: string) => {
    setExpandedErrorJobs((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const ingestionJobs = jobsData?.items || [];
  const modelRuns = runsData?.items || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
              Real-Time Pipeline & Job Monitoring
            </h2>
            <Badge variant="info">Live Polling (5s)</Badge>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Track background worker progress, rate-limiting heartbeats, and failure diagnostics.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowIngestModal(true)}
            leftIcon={<Download size={14} />}
          >
            New Ingestion Job
          </Button>

          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowAnalyzeModal(true)}
            leftIcon={<Sparkles size={14} />}
          >
            New Classification Run
          </Button>
        </div>
      </div>

      {/* Pipeline Tabs (Ingestion vs Gemini Analysis) */}
      <div className="card" style={{ padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button
            size="sm"
            variant={activeTab === 'ingestion' ? 'primary' : 'outline'}
            onClick={() => setActiveTab('ingestion')}
            leftIcon={<Download size={14} />}
          >
            Source Ingestion Jobs ({ingestionJobs.length})
          </Button>

          <Button
            size="sm"
            variant={activeTab === 'analysis' ? 'primary' : 'outline'}
            onClick={() => setActiveTab('analysis')}
            leftIcon={<Sparkles size={14} />}
          >
            Gemini Classification Runs ({modelRuns.length})
          </Button>
        </div>
      </div>

      {/* Tab 1: Ingestion Jobs List */}
      {activeTab === 'ingestion' && (
        <div>
          {isJobsLoading ? (
            <Spinner size="lg" label="Loading active jobs..." style={{ minHeight: '250px' }} />
          ) : ingestionJobs.length === 0 ? (
            <EmptyState
              title="No Ingestion Jobs Found"
              description="Start a new ingestion job to pull user reviews from Google Play, App Store, Reddit, or forums."
              actionLabel="Launch Ingestion Job"
              onAction={() => setShowIngestModal(true)}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {ingestionJobs.map((job) => {
                const isRunning = job.status === 'running' || job.status === 'queued';
                const isFailed = job.status === 'failed';
                const hasError = !!job.error_details;
                const isExpanded = !!expandedErrorJobs[job.id];
                const percent = job.progress_percent || (job.status === 'completed' ? 100 : 35);

                return (
                  <div
                    key={job.id}
                    className="card"
                    style={{
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.85rem',
                      border: isRunning
                        ? '1px solid var(--border-focus)'
                        : isFailed
                        ? '1px solid rgba(239, 68, 68, 0.4)'
                        : '1px solid var(--border-subtle)',
                    }}
                  >
                    {/* Top Row: Type, Status, Duration */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <SourceBadge platform={job.source_type} />
                        <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                          Job #{job.id.substring(0, 8)}
                        </span>
                        <Badge
                          variant={
                            job.status === 'completed'
                              ? 'success'
                              : job.status === 'running'
                              ? 'info'
                              : job.status === 'failed'
                              ? 'danger'
                              : 'warning'
                          }
                        >
                          {job.status.toUpperCase()}
                        </Badge>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Clock size={13} /> Started: {new Date(job.started_at || job.created_at || Date.now()).toLocaleTimeString()}
                        </span>

                        {isRunning && (
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => setCancellingJobId(job.id)}
                            leftIcon={<XCircle size={13} />}
                          >
                            Cancel Job
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                        <span>
                          Stored <strong>{job.records_stored}</strong> / Found <strong>{job.records_found}</strong> records
                        </span>
                        <span>{percent}%</span>
                      </div>
                      <div
                        style={{
                          height: '6px',
                          background: 'var(--bg-tertiary)',
                          borderRadius: '9999px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${percent}%`,
                            background:
                              isFailed
                                ? 'var(--status-danger)'
                                : job.status === 'completed'
                                ? 'var(--status-success)'
                                : 'var(--accent-primary)',
                            transition: 'width 0.5s ease',
                          }}
                        />
                      </div>
                    </div>

                    {/* Error Accordion */}
                    {hasError && (
                      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.6rem' }}>
                        <button
                          onClick={() => toggleError(job.id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#f87171',
                            fontSize: '0.8rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            cursor: 'pointer',
                          }}
                        >
                          <AlertTriangle size={14} />
                          <span>{isExpanded ? 'Hide Error Diagnostics' : 'View Failure Logs & Diagnostics'}</span>
                          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>

                        {isExpanded && (
                          <pre
                            style={{
                              marginTop: '0.5rem',
                              padding: '0.75rem',
                              background: 'rgba(239, 68, 68, 0.08)',
                              borderRadius: 'var(--radius-md)',
                              fontSize: '0.775rem',
                              color: '#fca5a5',
                              overflowX: 'auto',
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            {JSON.stringify(job.error_details, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Gemini Analysis Model Runs */}
      {activeTab === 'analysis' && (
        <div>
          {isRunsLoading ? (
            <Spinner size="lg" label="Loading analysis runs..." style={{ minHeight: '250px' }} />
          ) : modelRuns.length === 0 ? (
            <EmptyState
              icon={<Sparkles size={32} color="var(--accent-primary)" />}
              title="No AI Classification Runs"
              description="Run the Gemini worker to execute 2-stage classification, 12-field extraction, and 768-d vector embedding generation."
              actionLabel="Launch AI Worker"
              onAction={() => setShowAnalyzeModal(true)}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {modelRuns.map((run) => {
                const isRunning = run.status === 'running' || run.status === 'queued';
                const isPaused = run.status === 'paused';
                const isCompleted = run.status === 'completed';
                const percent =
                  run.total_records > 0
                    ? Math.round((run.processed_records / run.total_records) * 100)
                    : isCompleted
                    ? 100
                    : 0;

                return (
                  <div
                    key={run.id}
                    className="card"
                    style={{
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.85rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <Badge variant="purple">{run.model_name || 'Gemini 1.5 Pro'}</Badge>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                          Prompt v{run.prompt_version || '1.0.0'}
                        </span>
                        <Badge variant={isCompleted ? 'success' : isRunning ? 'info' : isPaused ? 'warning' : 'danger'}>
                          {run.status.toUpperCase()}
                        </Badge>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        {isPaused && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => resumeRunMutation.mutate(run.id)}
                            leftIcon={<RotateCcw size={13} />}
                          >
                            Resume Worker
                          </Button>
                        )}
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          Started: {new Date(run.started_at || run.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                        <span>
                          Processed <strong>{run.processed_records}</strong> of <strong>{run.total_records}</strong> records (<strong>{run.relevant_records}</strong> relevant evidence found)
                        </span>
                        <span>{percent}%</span>
                      </div>
                      <div
                        style={{
                          height: '6px',
                          background: 'var(--bg-tertiary)',
                          borderRadius: '9999px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${percent}%`,
                            background: isCompleted ? 'var(--status-success)' : 'var(--accent-gradient)',
                            transition: 'width 0.5s ease',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Ingest Modal */}
      <Modal
        isOpen={showIngestModal}
        onClose={() => setShowIngestModal(false)}
        title="Start Source Ingestion Job"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowIngestModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => createJobMutation.mutate()}
              isLoading={createJobMutation.isPending}
            >
              Start Job
            </Button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Select Source Platform Adapter
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
              <option value="youtube">YouTube Video Transcripts</option>
              <option value="forum">Support Forum Threads</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Adapter Parameters (JSON)
            </label>
            <textarea
              rows={4}
              value={ingestConfig}
              onChange={(e) => setIngestConfig(e.target.value)}
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

      {/* Analyze Modal */}
      <Modal
        isOpen={showAnalyzeModal}
        onClose={() => setShowAnalyzeModal(false)}
        title="Launch Gemini AI Classification Run"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowAnalyzeModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => startAnalysisMutation.mutate()}
              isLoading={startAnalysisMutation.isPending}
            >
              Launch Analysis Worker
            </Button>
          </>
        }
      >
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          Dispatches asynchronous Gemini 1.5 Pro pipeline across all unanalyzed source records.
          Jobs run with automated exponential backoff and rate-limit recovery.
        </p>
      </Modal>

      {/* Cancel Confirmation Modal */}
      {cancellingJobId && (
        <Modal
          isOpen={!!cancellingJobId}
          onClose={() => setCancellingJobId(null)}
          title="Confirm Job Cancellation"
          footer={
            <>
              <Button variant="ghost" onClick={() => setCancellingJobId(null)}>
                Dismiss
              </Button>
              <Button
                variant="danger"
                onClick={() => cancelJobMutation.mutate(cancellingJobId)}
                isLoading={cancelJobMutation.isPending}
              >
                Cancel Running Job
              </Button>
            </>
          }
        >
          <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
            Are you sure you want to stop this running ingestion job? Any records already stored will be safely retained.
          </p>
        </Modal>
      )}
    </div>
  );
}
