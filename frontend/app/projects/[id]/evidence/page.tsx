'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Eye,
  Tag,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvidenceRecord, RetrievalOutcome } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ConfidenceBadge } from '@/components/ui/ConfidenceBadge';
import { OutcomeBadge } from '@/components/ui/OutcomeBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { Pagination } from '@/components/ui/Pagination';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';

export default function EvidenceViewerPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // URL state
  const page = parseInt(searchParams.get('page') || '1', 10);
  const outcome = searchParams.get('outcome') || '';
  const search = searchParams.get('search') || '';
  const failurePoint = searchParams.get('failure_point') || '';
  const needsReview = searchParams.get('needs_review');
  const confMin = searchParams.get('confidence_min') ? parseFloat(searchParams.get('confidence_min')!) : undefined;

  const [searchInput, setSearchInput] = useState(search);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  const updateFilters = (updates: Record<string, string | null>) => {
    const current = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, val]) => {
      if (val === null || val === '') {
        current.delete(key);
      } else {
        current.set(key, val);
      }
    });
    if (!('page' in updates)) {
      current.set('page', '1');
    }
    router.push(`${pathname}?${current.toString()}`);
  };

  const clearAllFilters = () => {
    router.push(pathname);
    setSearchInput('');
  };

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['evidence-records', projectId, page, outcome, search, failurePoint, needsReview, confMin],
    queryFn: () =>
      api.getEvidenceRecords(projectId, {
        page,
        page_size: 50,
        outcome: outcome || undefined,
        search: search || undefined,
        failure_point: failurePoint || undefined,
        needs_review: needsReview === 'true' ? true : needsReview === 'false' ? false : undefined,
        confidence_min: confMin,
      }),
    enabled: !!projectId,
    placeholderData: (prev) => prev,
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'approved' | 'rejected' }) =>
      api.submitReview(projectId, id, { action }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-records', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      setSelectedEvidence(null);
    },
  });

  const toggleExpand = (id: string) => {
    setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const activeFiltersCount = [outcome, search, failurePoint, needsReview, confMin !== undefined].filter(Boolean).length;

  // Helper to identify False Positive Clutter
  const isFalsePositiveClutter = (record: EvidenceRecord) => {
    if (record.failure_points?.some((fp) => fp.includes('false_positive') || fp.includes('clutter') || fp.includes('noise'))) {
      return true;
    }
    const content = (record.raw_content || record.evidence_excerpt || '').toLowerCase();
    return (
      content.includes('every picture') ||
      content.includes('random photos') ||
      content.includes('45 photos') ||
      content.includes('300 blue') ||
      content.includes('burying the actual') ||
      content.includes('gave me every') ||
      content.includes('returned every')
    );
  };

  // Highlight excerpt inside raw text
  const renderHighlightedText = (raw: string = '', excerpt: string | null = '') => {
    if (!excerpt || !raw.includes(excerpt)) {
      return <span>{raw}</span>;
    }
    const parts = raw.split(excerpt);
    return (
      <span>
        {parts[0]}
        <mark
          style={{
            background: 'rgba(251, 188, 5, 0.25)',
            color: '#fef08a',
            border: '1px solid rgba(251, 188, 5, 0.4)',
            padding: '2px 4px',
            borderRadius: '4px',
            fontWeight: 600,
          }}
        >
          {excerpt}
        </mark>
        {parts.slice(1).join(excerpt)}
      </span>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Quick Diagnostic Pill Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => updateFilters({ failure_point: failurePoint === 'false_positive_clutter' ? null : 'false_positive_clutter' })}
          style={{
            padding: '0.4rem 0.85rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            cursor: 'pointer',
            border: failurePoint === 'false_positive_clutter' ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
            background: failurePoint === 'false_positive_clutter' ? 'rgba(239, 68, 68, 0.2)' : 'var(--bg-tertiary)',
            color: failurePoint === 'false_positive_clutter' ? '#fca5a5' : 'var(--text-secondary)',
          }}
        >
          <AlertTriangle size={13} color={failurePoint === 'false_positive_clutter' ? '#ef4444' : 'var(--text-muted)'} />
          <span>🚨 Too Many Random Photos (Search Clutter)</span>
        </button>

        <button
          type="button"
          onClick={() => updateFilters({ needs_review: needsReview === 'true' ? null : 'true' })}
          style={{
            padding: '0.4rem 0.85rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            cursor: 'pointer',
            border: needsReview === 'true' ? '1px solid #f59e0b' : '1px solid var(--border-subtle)',
            background: needsReview === 'true' ? 'rgba(245, 158, 11, 0.2)' : 'var(--bg-tertiary)',
            color: needsReview === 'true' ? '#fde68a' : 'var(--text-secondary)',
          }}
        >
          <ShieldCheck size={13} color={needsReview === 'true' ? '#f59e0b' : 'var(--text-muted)'} />
          <span>⚠️ Needs Double-Check (&lt; 70% Confidence)</span>
        </button>

        <button
          type="button"
          onClick={() => updateFilters({ outcome: outcome === 'gave_up' ? null : 'gave_up' })}
          style={{
            padding: '0.4rem 0.85rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            cursor: 'pointer',
            border: outcome === 'gave_up' ? '1px solid #8b5cf6' : '1px solid var(--border-subtle)',
            background: outcome === 'gave_up' ? 'rgba(139, 92, 246, 0.2)' : 'var(--bg-tertiary)',
            color: outcome === 'gave_up' ? '#c4b5fd' : 'var(--text-secondary)',
          }}
        >
          <XCircle size={13} color={outcome === 'gave_up' ? '#8b5cf6' : 'var(--text-muted)'} />
          <span>Gave Up Searching</span>
        </button>
      </div>

      {/* Filters Header Card */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '1rem',
          }}
        >
          {/* Search Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateFilters({ search: searchInput.trim() || null });
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              flex: '1 1 320px',
              maxWidth: '500px',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.45rem 0.8rem',
                background: 'var(--bg-tertiary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                width: '100%',
              }}
            >
              <Search size={16} style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search user complaints or keywords..."
                style={{
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  width: '100%',
                }}
              />
            </div>
            <Button type="submit" size="sm" variant="secondary">
              Search
            </Button>
          </form>

          {/* Filter Status Badge */}
          {activeFiltersCount > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Badge variant="warning">{activeFiltersCount} filter(s) active</Badge>
              <Button size="sm" variant="ghost" onClick={clearAllFilters} leftIcon={<RotateCcw size={14} />}>
                Clear Filters
              </Button>
            </div>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Outcome Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Outcome:</span>
            <select
              value={outcome}
              onChange={(e) => updateFilters({ outcome: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All Outcomes</option>
              <option value="gave_up">Gave up searching</option>
              <option value="found_after_effort">Found after lots of scrolling</option>
              <option value="never_found">Could not find photo at all</option>
              <option value="found_alternative">Used a workaround</option>
              <option value="found_quickly">Found easily</option>
            </select>
          </div>

          {/* Human Review Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Review Status:</span>
            <select
              value={needsReview || ''}
              onChange={(e) => updateFilters({ needs_review: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All Review States</option>
              <option value="true">Needs Double-Check Only</option>
              <option value="false">Confirmed / High Confidence Only</option>
            </select>
          </div>

          {/* Failure Point / False Positive Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Issue Type:</span>
            <select
              value={failurePoint}
              onChange={(e) => updateFilters({ failure_point: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All Issue Types</option>
              <option value="false_positive_clutter">🚨 Too Many Random Photos (Search Clutter)</option>
              <option value="multi_attribute_conjunction_failure">Multiple Details Search Problem</option>
              <option value="temporal_ambiguity">Forgotten Dates &amp; Life Moments</option>
              <option value="ocr_background_noise">Signs &amp; Documents Mixed In</option>
              <option value="pet_face_clustering_error">Similar Pets / Faces Mixed Up</option>
              <option value="negative_filtering_unsupported">Cannot Exclude Things (No &apos;NOT&apos;)</option>
            </select>
          </div>

          {/* Confidence Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AI Confidence:</span>
            <select
              value={confMin !== undefined ? confMin.toString() : ''}
              onChange={(e) => updateFilters({ confidence_min: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">Any Confidence</option>
              <option value="0.7">High Confidence (&ge; 70%)</option>
              <option value="0.85">Very High Confidence (&ge; 85%)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Evidence Cards Grid */}
      {isLoading ? (
        <Spinner size="lg" label="Loading evidence records..." style={{ minHeight: '300px' }} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No Evidence Records Match Filter"
          description="Adjust your filters or run a new Gemini AI classification job to extract more evidence."
          actionLabel="Clear Filters"
          onAction={clearAllFilters}
        />
      ) : (
        <div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            {data.items.map((record) => {
              const isExpanded = !!expandedCards[record.id];
              const isFPClutter = isFalsePositiveClutter(record);

              return (
                <div
                  key={record.id}
                  className="card"
                  style={{
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '1rem',
                    border: record.needs_human_review
                      ? '1px solid rgba(245, 158, 11, 0.4)'
                      : isFPClutter
                      ? '1px solid rgba(239, 68, 68, 0.35)'
                      : '1px solid var(--border-subtle)',
                  }}
                >
                  <div>
                    {/* Header: Confidence + Outcome + FP Badges */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '0.5rem',
                        marginBottom: '0.75rem',
                        flexWrap: 'wrap',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                        <ConfidenceBadge score={record.confidence_score} size="sm" />
                        <OutcomeBadge outcome={record.retrieval_outcome} size="sm" />
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        {isFPClutter && (
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              padding: '0.2rem 0.5rem',
                              background: 'rgba(239, 68, 68, 0.15)',
                              color: '#f87171',
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              borderRadius: '4px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                            }}
                          >
                            <AlertTriangle size={11} /> False Positive Clutter
                          </span>
                        )}
                        {record.needs_human_review && (
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 600,
                              padding: '0.2rem 0.45rem',
                              background: 'rgba(245, 158, 11, 0.15)',
                              color: '#fbbf24',
                              border: '1px solid rgba(245, 158, 11, 0.3)',
                              borderRadius: '4px',
                            }}
                          >
                            Review Needed
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Scenario Title */}
                    <h4
                      style={{
                        fontSize: '0.95rem',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                        lineHeight: 1.4,
                        marginBottom: '0.6rem',
                      }}
                    >
                      {record.retrieval_scenario || 'Uncategorized Retrieval Scenario'}
                    </h4>

                    {/* Verbatim Excerpt Callout */}
                    {record.evidence_excerpt && (
                      <div
                        style={{
                          padding: '0.65rem 0.85rem',
                          background: 'rgba(255, 255, 255, 0.03)',
                          borderLeft: '3px solid var(--google-yellow, #fbbc05)',
                          borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                          fontSize: '0.85rem',
                          fontStyle: 'italic',
                          color: '#fef08a',
                          lineHeight: 1.5,
                          marginBottom: '0.75rem',
                        }}
                      >
                        &ldquo;{record.evidence_excerpt}&rdquo;
                      </div>
                    )}

                    {/* Failure Points Badges */}
                    {record.failure_points && record.failure_points.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
                        {record.failure_points.map((fp, idx) => (
                          <span
                            key={idx}
                            style={{
                              fontSize: '0.7rem',
                              padding: '0.15rem 0.45rem',
                              background: fp.includes('false_positive') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(239, 68, 68, 0.08)',
                              color: fp.includes('false_positive') ? '#fca5a5' : '#fca5a5',
                              border: '1px solid rgba(239, 68, 68, 0.2)',
                              borderRadius: '4px',
                              fontWeight: fp.includes('false_positive') ? 600 : 400,
                            }}
                          >
                            {fp.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Expandable Memory Cues Preview */}
                    {isExpanded && (
                      <div
                        style={{
                          padding: '0.75rem',
                          background: 'var(--bg-tertiary)',
                          borderRadius: 'var(--radius-md)',
                          fontSize: '0.8rem',
                          marginBottom: '0.75rem',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.4rem',
                        }}
                      >
                        <div>
                          <strong>Gemini Rationale:</strong> {record.rationale}
                        </div>
                        {record.missing_information && (
                          <div>
                            <strong>Missing Info:</strong> {record.missing_information}
                          </div>
                        )}
                        {record.user_segment && (
                          <div>
                            <strong>User Segment:</strong> {record.user_segment}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Card Actions Footer */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      borderTop: '1px solid var(--border-subtle)',
                      paddingTop: '0.75rem',
                    }}
                  >
                    <button
                      onClick={() => toggleExpand(record.id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        fontSize: '0.75rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.2rem',
                        cursor: 'pointer',
                      }}
                    >
                      {isExpanded ? (
                        <>
                          Less details <ChevronUp size={14} />
                        </>
                      ) : (
                        <>
                          More details <ChevronDown size={14} />
                        </>
                      )}
                    </button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedEvidence(record)}
                      leftIcon={<Eye size={13} />}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Server Pagination Controls */}
          <Pagination
            currentPage={data.page}
            totalPages={data.total_pages}
            totalItems={data.total}
            pageSize={data.page_size}
            onPageChange={(p) => updateFilters({ page: p.toString() })}
            isLoading={isPlaceholderData}
          />
        </div>
      )}

      {/* Full 12-Field Evidence Detail & False Positive Diagnostic Modal */}
      {selectedEvidence && (
        <Modal
          isOpen={!!selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
          maxWidth="750px"
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Sparkles size={18} color="var(--accent-primary)" />
              <span>User Review Story &amp; Details</span>
            </div>
          }
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  size="sm"
                  variant="success"
                  onClick={() => reviewMutation.mutate({ id: selectedEvidence.id, action: 'approved' })}
                  isLoading={reviewMutation.isPending}
                  leftIcon={<CheckCircle2 size={14} />}
                >
                  Confirm Genuine Problem
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => reviewMutation.mutate({ id: selectedEvidence.id, action: 'rejected' })}
                  isLoading={reviewMutation.isPending}
                  leftIcon={<XCircle size={14} />}
                >
                  Mark as Irrelevant / AI Mistake
                </Button>
              </div>
              <Button variant="primary" onClick={() => setSelectedEvidence(null)}>
                Done
              </Button>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Badges strip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <ConfidenceBadge score={selectedEvidence.confidence_score} />
              <OutcomeBadge outcome={selectedEvidence.retrieval_outcome} />
              {selectedEvidence.source_platform && <SourceBadge platform={selectedEvidence.source_platform} />}
              {isFalsePositiveClutter(selectedEvidence) && (
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.2rem 0.6rem',
                    background: 'rgba(239, 68, 68, 0.2)',
                    color: '#fca5a5',
                    border: '1px solid #ef4444',
                    borderRadius: '4px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                  }}
                >
                  <AlertTriangle size={12} /> Search Clutter (Returned Too Many Random Photos)
                </span>
              )}
            </div>

            {/* False Positive Diagnostic Card */}
            <div
              style={{
                padding: '1rem',
                background: isFalsePositiveClutter(selectedEvidence)
                  ? 'rgba(239, 68, 68, 0.08)'
                  : 'rgba(66, 133, 244, 0.08)',
                border: isFalsePositiveClutter(selectedEvidence)
                  ? '1px solid rgba(239, 68, 68, 0.3)'
                  : '1px solid rgba(66, 133, 244, 0.3)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
                Search Error Breakdown
              </div>
              <div style={{ fontSize: '0.85rem', lineHeight: 1.5, color: 'var(--text-primary)' }}>
                {isFalsePositiveClutter(selectedEvidence) ? (
                  <div>
                    <strong style={{ color: '#f87171' }}>🚨 Issue: Too Many Irrelevant Photos (Clutter Flood)</strong>
                    <p style={{ marginTop: '0.25rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      The search returned hundreds of unrelated photos (e.g. any picture of rain or street signs) which buried the photo the user was looking for.
                    </p>
                  </div>
                ) : (
                  <div>
                    <strong style={{ color: '#60a5fa' }}>🔍 Issue: Zero Photos Found (Missed Photo)</strong>
                    <p style={{ marginTop: '0.25rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      The search returned zero or no matches because the user did not know the exact calendar date or used descriptive words the app didn’t recognize.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Original raw content with verbatim highlight */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                FULL USER REVIEW (KEY PART HIGHLIGHTED)
              </div>
              <div
                style={{
                  padding: '1rem',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                }}
              >
                {renderHighlightedText(
                  selectedEvidence.raw_content || selectedEvidence.evidence_excerpt || '',
                  selectedEvidence.evidence_excerpt
                )}
              </div>
            </div>

            {/* 12-Field Structured Table */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                12 ANALYSIS DETAILS FROM USER STORY
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '0.75rem',
                  background: 'var(--bg-tertiary)',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.825rem',
                }}
              >
                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Retrieval Scenario:</strong>
                  <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                    {selectedEvidence.retrieval_scenario || 'N/A'}
                  </div>
                </div>

                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>User Segment:</strong>
                  <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                    {selectedEvidence.user_segment || 'General User'}
                  </div>
                </div>

                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Search Behavior:</strong>
                  <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                    {selectedEvidence.search_behavior || 'Natural Language Query'}
                  </div>
                </div>

                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Missing Information:</strong>
                  <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                    {selectedEvidence.missing_information || 'None identified'}
                  </div>
                </div>

                <div style={{ gridColumn: 'span 2' }}>
                  <strong style={{ color: 'var(--text-secondary)' }}>Memory Cues Recalled:</strong>
                  <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {Object.entries(selectedEvidence.memory_cues || {}).map(([cue, val]) => (
                      <span
                        key={cue}
                        style={{
                          padding: '0.2rem 0.5rem',
                          background: 'rgba(66, 133, 244, 0.1)',
                          border: '1px solid rgba(66, 133, 244, 0.25)',
                          color: '#93c5fd',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                        }}
                      >
                        <strong>{cue}:</strong> {String(val)}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ gridColumn: 'span 2' }}>
                  <strong style={{ color: 'var(--text-secondary)' }}>Failure Points:</strong>
                  <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {selectedEvidence.failure_points?.map((fp, i) => (
                      <Badge key={i} variant={fp.includes('false_positive') ? 'danger' : 'neutral'} size="sm">
                        {fp}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div style={{ gridColumn: 'span 2' }}>
                  <strong style={{ color: 'var(--text-secondary)' }}>Gemini Classification Rationale:</strong>
                  <div style={{ color: 'var(--text-primary)', marginTop: '2px', lineHeight: 1.5 }}>
                    {selectedEvidence.rationale}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
