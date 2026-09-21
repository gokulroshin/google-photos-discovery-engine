'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Code,
  Copy,
  BookOpen,
} from 'lucide-react';
import { api } from '@/lib/api';
import { ResearchReport } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Alert } from '@/components/ui/Alert';

export default function ResearchReportPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const queryClient = useQueryClient();

  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'markdown' | 'json'>('preview');

  const { data: stats } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => api.getProjectStats(projectId),
    enabled: !!projectId,
  });

  const { data: report, isLoading } = useQuery({
    queryKey: ['research-report', projectId],
    queryFn: () => api.getLatestReport(projectId),
    enabled: !!projectId,
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateReport(projectId),
    onSuccess: (data) => {
      queryClient.setQueryData(['research-report', projectId], data);
    },
  });

  const handleCopyMarkdown = () => {
    if (!report?.markdown) return;
    navigator.clipboard.writeText(report.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!report?.markdown) return;
    const blob = new Blob([report.markdown], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `research_report_${projectId}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `research_report_${projectId}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Strip */}
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
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
            Executive Research Report & Synthesis
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Traceable discovery report consolidating problem taxonomy, opportunity scoring, and evidence provenance.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Button
            size="sm"
            variant="outline"
            onClick={handleCopyMarkdown}
            disabled={!report}
            leftIcon={copied ? <CheckCircle2 size={14} color="#10b981" /> : <Copy size={14} />}
          >
            {copied ? 'Copied MD' : 'Copy Markdown'}
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={handleDownloadMarkdown}
            disabled={!report}
            leftIcon={<Download size={14} />}
          >
            Download .md
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={handleDownloadJSON}
            disabled={!report}
            leftIcon={<Code size={14} />}
          >
            Download .json
          </Button>

          <Button
            size="sm"
            variant="primary"
            onClick={() => generateMutation.mutate()}
            isLoading={generateMutation.isPending}
            leftIcon={<Sparkles size={14} />}
          >
            Generate Fresh Report
          </Button>
        </div>
      </div>

      {/* Warnings */}
      {stats?.warnings?.is_partial_dataset && (
        <Alert variant="warning" title="Report Generated on Partial Dataset">
          This report was generated while ingestion or classification jobs were still active. Quantitative metrics reflect intermediate samples.
        </Alert>
      )}

      {stats?.warnings?.has_pending_reviews && (
        <Alert variant="warning" title={`${stats.warnings.pending_reviews_count} Unverified Classifications in Review Queue`}>
          Certain findings are based on unverified AI classifications pending human review.
        </Alert>
      )}

      {/* Report Body */}
      {isLoading || generateMutation.isPending ? (
        <Spinner size="lg" label="Synthesizing research report..." style={{ minHeight: '350px' }} />
      ) : !report ? (
        <EmptyState
          title="No Research Report Generated"
          description="Click 'Generate Fresh Report' to synthesize all current taxonomy categories, scored opportunities, and evidence excerpts."
          actionLabel="Generate Report Now"
          onAction={() => generateMutation.mutate()}
        />
      ) : (
        <div className="card" style={{ padding: '2rem' }}>
          {/* View Mode Switcher */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid var(--border-subtle)',
              paddingBottom: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Button
                size="sm"
                variant={activeTab === 'preview' ? 'primary' : 'outline'}
                onClick={() => setActiveTab('preview')}
                leftIcon={<BookOpen size={14} />}
              >
                Rendered Report Preview
              </Button>
              <Button
                size="sm"
                variant={activeTab === 'markdown' ? 'primary' : 'outline'}
                onClick={() => setActiveTab('markdown')}
                leftIcon={<FileText size={14} />}
              >
                Raw Markdown
              </Button>
              <Button
                size="sm"
                variant={activeTab === 'json' ? 'primary' : 'outline'}
                onClick={() => setActiveTab('json')}
                leftIcon={<Code size={14} />}
              >
                Structured JSON
              </Button>
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Generated: {report.generated_at}
            </div>
          </div>

          {/* Tab 1: Rendered Report Preview */}
          {activeTab === 'preview' && (
            <div
              style={{
                lineHeight: 1.7,
                fontSize: '0.95rem',
                color: 'var(--text-primary)',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.5rem',
              }}
            >
              {/* Executive Summary */}
              <div>
                <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '0.5rem' }}>
                  {report.project_name} — Research Discovery Report
                </h1>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                  <Badge variant="purple">Google Photos Discovery Engine</Badge>
                  <Badge variant="info">{report.categories_count} Problem Categories</Badge>
                  <Badge variant="success">{report.opportunities_count} Opportunity Areas</Badge>
                </div>
              </div>

              {/* Taxonomy Summary Section */}
              <div style={{ padding: '1.5rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--google-blue)' }}>
                  1. Empirical Retrieval Problem Taxonomy
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {report.categories.map((c, i) => (
                    <div key={i} style={{ borderBottom: i < report.categories.length - 1 ? '1px solid var(--border-subtle)' : 'none', paddingBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <strong style={{ fontSize: '1rem' }}>{c.name}</strong>
                        <Badge variant={c.confidence_level === 'high' ? 'success' : 'info'}>
                          {c.evidence_count} evidence records
                        </Badge>
                      </div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                        {c.definition}
                      </p>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        <strong>Failure Mechanism:</strong> {c.failure_mechanism}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Opportunity Scoring Section */}
              <div style={{ padding: '1.5rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--status-success)' }}>
                  2. Scored Opportunity Areas
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {report.opportunities.map((o, i) => (
                    <div key={i} style={{ borderBottom: i < report.opportunities.length - 1 ? '1px solid var(--border-subtle)' : 'none', paddingBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <strong style={{ fontSize: '1rem' }}>{o.name}</strong>
                        <Badge variant={o.status === 'validated' ? 'success' : 'warning'}>
                          Impact: {o.user_impact_score}/10
                        </Badge>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.5rem', fontSize: '0.8rem', marginTop: '0.5rem', color: 'var(--text-secondary)' }}>
                        <div><strong>Strategic Fit:</strong> {o.strategic_relevance}/10</div>
                        <div><strong>Abandonment:</strong> {Math.round((o.abandonment_rate || 0) * 100)}%</div>
                        <div><strong>Reach:</strong> {o.potential_reach}</div>
                        <div><strong>Validation Effort:</strong> {o.validation_effort?.toUpperCase()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Raw Markdown */}
          {activeTab === 'markdown' && (
            <pre
              style={{
                padding: '1.25rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                lineHeight: 1.6,
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
              }}
            >
              {report.markdown}
            </pre>
          )}

          {/* Tab 3: Structured JSON */}
          {activeTab === 'json' && (
            <pre
              style={{
                padding: '1.25rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: '#60a5fa',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                lineHeight: 1.6,
                overflowX: 'auto',
              }}
            >
              {JSON.stringify(report, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
