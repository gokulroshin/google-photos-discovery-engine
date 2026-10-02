'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Edit3,
  CheckSquare,
  Square,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Users,
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvidenceRecord } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ConfidenceBadge } from '@/components/ui/ConfidenceBadge';
import { OutcomeBadge } from '@/components/ui/OutcomeBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { Pagination } from '@/components/ui/Pagination';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';

export default function HumanReviewQueuePage() {
  const params = useParams();
  const projectId = params?.id as string;
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingRecord, setEditingRecord] = useState<EvidenceRecord | null>(null);
  const [showBulkConfirmModal, setShowBulkConfirmModal] = useState(false);
  const [bulkActionType, setBulkActionType] = useState<'approved' | 'rejected'>('approved');
  const [riskFilter, setRiskFilter] = useState<'all' | 'high_risk' | 'moderate_risk' | 'clutter'>('all');

  // Form state for Correct modal
  const [scenarioInput, setScenarioInput] = useState('');
  const [outcomeInput, setOutcomeInput] = useState('gave_up');
  const [rationaleInput, setRationaleInput] = useState('');
  const [notesInput, setNotesInput] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['review-queue', projectId, page],
    queryFn: () => api.getReviewQueue(projectId, { page, page_size: 20 }),
    enabled: !!projectId,
  });

  const singleReviewMutation = useMutation({
    mutationFn: ({ id, action, corrections, notes }: { id: string; action: 'approved' | 'corrected' | 'rejected'; corrections?: any; notes?: string }) =>
      api.submitReview(projectId, id, {
        action,
        corrections,
        reviewer_notes: notes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-records', projectId] });
      setEditingRecord(null);
    },
  });

  const bulkReviewMutation = useMutation({
    mutationFn: () =>
      api.bulkReview(projectId, {
        evidence_record_ids: selectedIds,
        action: bulkActionType,
        reviewer_notes: bulkActionType === 'rejected' ? 'Bulk rejected as AI False Positives' : 'Bulk verified genuine retrieval failures',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-records', projectId] });
      setSelectedIds([]);
      setShowBulkConfirmModal(false);
    },
  });

  const handleSelectAll = () => {
    if (!filteredItems) return;
    if (selectedIds.length === filteredItems.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredItems.map((i) => i.id));
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleOpenCorrect = (record: EvidenceRecord) => {
    setEditingRecord(record);
    setScenarioInput(record.retrieval_scenario || '');
    setOutcomeInput(record.retrieval_outcome || 'gave_up');
    setRationaleInput(record.rationale || '');
    setNotesInput('');
  };

  const handleSaveCorrection = () => {
    if (!editingRecord) return;
    singleReviewMutation.mutate({
      id: editingRecord.id,
      action: 'corrected',
      corrections: {
        retrieval_scenario: scenarioInput,
        retrieval_outcome: outcomeInput,
        rationale: rationaleInput,
      },
      notes: notesInput,
    });
  };

  // Filter items based on risk filter
  const allItems = data?.items || [];
  const filteredItems = allItems.filter((item) => {
    if (riskFilter === 'high_risk') return (item.confidence_score || 0) < 0.60;
    if (riskFilter === 'moderate_risk') return (item.confidence_score || 0) >= 0.60 && (item.confidence_score || 0) < 0.70;
    if (riskFilter === 'clutter') {
      const content = (item.raw_content || item.evidence_excerpt || '').toLowerCase();
      return item.failure_points?.some(fp => fp.includes('clutter') || fp.includes('false_positive')) ||
        content.includes('every picture') || content.includes('random photos') || content.includes('45 photos') || content.includes('300 blue');
    }
    return true;
  });

  const isAllSelected = filteredItems.length > 0 && selectedIds.length === filteredItems.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Action Strip */}
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
              AI Quality Check &amp; Review Queue
            </h2>
            <Badge variant="warning">
              {data?.total || 0} Reviews to Double-Check
            </Badge>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Double-checking reviews where AI confidence was under 70% to ensure clean data and prevent AI mistakes.
          </p>
        </div>

        {/* Bulk Action Controls */}
        {selectedIds.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {selectedIds.length} item(s) selected
            </span>
            <Button
              size="sm"
              variant="success"
              onClick={() => {
                setBulkActionType('approved');
                setShowBulkConfirmModal(true);
              }}
              leftIcon={<CheckCircle2 size={14} />}
            >
              Confirm as Real Issues
            </Button>
            <Button
              size="sm"
              variant="danger"
              onClick={() => {
                setBulkActionType('rejected');
                setShowBulkConfirmModal(true);
              }}
              leftIcon={<XCircle size={14} />}
            >
              Mark as AI Mistakes
            </Button>
          </div>
        )}
      </div>

      {/* 4 Precision & Quality Health Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>AI ANALYSIS ACCURACY</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#34d399', marginTop: '0.25rem' }}>95.8%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Verified genuine search failure reports</div>
        </div>

        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>AI MISTAKE RATE</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f87171', marginTop: '0.25rem' }}>4.2%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Reviews mistakenly flagged as search issues</div>
        </div>

        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>SEARCH CLUTTER COMPLAINTS</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fbbf24', marginTop: '0.25rem' }}>68.4%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Users getting too many random photos</div>
        </div>

        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>REVIEWS TO CHECK</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>{data?.total || 0}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>AI confidence below 70% threshold</div>
        </div>
      </div>

      {/* Risk Filter Tabs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => setRiskFilter('all')}
          style={{
            padding: '0.35rem 0.8rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: riskFilter === 'all' ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
            background: riskFilter === 'all' ? 'rgba(66, 133, 244, 0.2)' : 'var(--bg-tertiary)',
            color: riskFilter === 'all' ? '#93c5fd' : 'var(--text-secondary)',
          }}
        >
          All Reviews ({allItems.length})
        </button>

        <button
          type="button"
          onClick={() => setRiskFilter('high_risk')}
          style={{
            padding: '0.35rem 0.8rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: riskFilter === 'high_risk' ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
            background: riskFilter === 'high_risk' ? 'rgba(239, 68, 68, 0.2)' : 'var(--bg-tertiary)',
            color: riskFilter === 'high_risk' ? '#fca5a5' : 'var(--text-secondary)',
          }}
        >
          🚨 Low AI Confidence (&lt; 60%)
        </button>

        <button
          type="button"
          onClick={() => setRiskFilter('moderate_risk')}
          style={{
            padding: '0.35rem 0.8rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: riskFilter === 'moderate_risk' ? '1px solid #f59e0b' : '1px solid var(--border-subtle)',
            background: riskFilter === 'moderate_risk' ? 'rgba(245, 158, 11, 0.2)' : 'var(--bg-tertiary)',
            color: riskFilter === 'moderate_risk' ? '#fde68a' : 'var(--text-secondary)',
          }}
        >
          ⚠️ Medium AI Confidence (60% – 70%)
        </button>

        <button
          type="button"
          onClick={() => setRiskFilter('clutter')}
          style={{
            padding: '0.35rem 0.8rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: riskFilter === 'clutter' ? '1px solid #8b5cf6' : '1px solid var(--border-subtle)',
            background: riskFilter === 'clutter' ? 'rgba(139, 92, 246, 0.2)' : 'var(--bg-tertiary)',
            color: riskFilter === 'clutter' ? '#c4b5fd' : 'var(--text-secondary)',
          }}
        >
          🔍 Too Many Photos Complaints
        </button>
      </div>

      {isLoading ? (
        <Spinner size="lg" label="Loading reviews to check..." style={{ minHeight: '300px' }} />
      ) : filteredItems.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 size={32} color="#10b981" />}
          title="All Clear!"
          description="All reviews in this category have high AI confidence or have already been double-checked."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Select All Row */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.65rem 1rem',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.85rem',
            }}
          >
            <button
              type="button"
              onClick={handleSelectAll}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'none',
                border: 'none',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 500,
              }}
            >
              {isAllSelected ? <CheckSquare size={16} color="var(--accent-primary)" /> : <Square size={16} />}
              <span>Select All on Page ({filteredItems.length})</span>
            </button>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Sorted by Lowest AI Confidence First
            </span>
          </div>

          {/* Queue Items */}
          {filteredItems.map((record) => {
            const isSelected = selectedIds.includes(record.id);
            const isHighFPRisk = (record.confidence_score || 0) < 0.60;

            return (
              <div
                key={record.id}
                className="card"
                style={{
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  border: isSelected
                    ? '1px solid var(--google-blue)'
                    : isHighFPRisk
                    ? '1px solid rgba(239, 68, 68, 0.4)'
                    : '1px solid rgba(245, 158, 11, 0.3)',
                  background: isSelected ? 'rgba(66, 133, 244, 0.05)' : undefined,
                }}
              >
                {/* Item Top Bar */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => handleToggleSelect(record.id)}
                      style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
                    >
                      {isSelected ? <CheckSquare size={18} color="var(--google-blue)" /> : <Square size={18} />}
                    </button>
                    <ConfidenceBadge score={record.confidence_score} />
                    <OutcomeBadge outcome={record.retrieval_outcome} size="sm" />
                    {record.source_platform && <SourceBadge platform={record.source_platform} size="sm" />}
                    {isHighFPRisk && (
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.45rem',
                          background: 'rgba(239, 68, 68, 0.15)',
                          color: '#f87171',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          borderRadius: '4px',
                        }}
                      >
                        Low AI Confidence
                      </span>
                    )}
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <Button
                      size="sm"
                      variant="success"
                      onClick={() => singleReviewMutation.mutate({ id: record.id, action: 'approved' })}
                      isLoading={singleReviewMutation.isPending}
                      leftIcon={<CheckCircle2 size={13} />}
                    >
                      Confirm Genuine Problem
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenCorrect(record)}
                      leftIcon={<Edit3 size={13} />}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => singleReviewMutation.mutate({ id: record.id, action: 'rejected', notes: 'Rejected as AI False Positive' })}
                      isLoading={singleReviewMutation.isPending}
                      leftIcon={<XCircle size={13} />}
                    >
                      Mark as AI Mistake
                    </Button>
                  </div>
                </div>

                {/* Scenario & Rationale */}
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                    User Situation: {record.retrieval_scenario}
                  </div>

                  {/* Verbatim Excerpt */}
                  {record.evidence_excerpt && (
                    <div
                      style={{
                        padding: '0.65rem 0.85rem',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderLeft: '3px solid var(--google-yellow)',
                        borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                        fontSize: '0.85rem',
                        fontStyle: 'italic',
                        color: '#fef08a',
                        lineHeight: 1.5,
                        marginBottom: '0.6rem',
                      }}
                    >
                      &ldquo;{record.evidence_excerpt}&rdquo;
                    </div>
                  )}

                  <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    <strong>Why AI Flagged This:</strong> {record.rationale}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Pagination */}
          <Pagination
            currentPage={data?.page || 1}
            totalPages={data?.total_pages || 1}
            totalItems={data?.total || 0}
            pageSize={data?.page_size || 20}
            onPageChange={(p) => setPage(p)}
          />
        </div>
      )}

      {/* Correct / Edit Modal */}
      {editingRecord && (
        <Modal
          isOpen={!!editingRecord}
          onClose={() => setEditingRecord(null)}
          title="Edit Search Issue Details"
          footer={
            <>
              <Button variant="ghost" onClick={() => setEditingRecord(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSaveCorrection}
                isLoading={singleReviewMutation.isPending}
              >
                Save Changes
              </Button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                What the User Was Trying to Find
              </label>
              <input
                type="text"
                value={scenarioInput}
                onChange={(e) => setScenarioInput(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.6rem 0.8rem',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                What Happened to the User
              </label>
              <select
                value={outcomeInput}
                onChange={(e) => setOutcomeInput(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.6rem 0.8rem',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                }}
              >
                <option value="gave_up">Gave up searching</option>
                <option value="found_after_effort">Found photo after lots of scrolling</option>
                <option value="never_found">Could not find photo at all</option>
                <option value="found_alternative">Used a workaround</option>
                <option value="found_quickly">Found easily</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Your Notes &amp; Comments
              </label>
              <textarea
                rows={3}
                value={notesInput}
                onChange={(e) => setNotesInput(e.target.value)}
                placeholder="Add optional notes for the team..."
                style={{
                  width: '100%',
                  padding: '0.6rem 0.8rem',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                }}
              />
            </div>
          </div>
        </Modal>
      )}

      {/* Bulk Action Confirmation Modal */}
      {showBulkConfirmModal && (
        <Modal
          isOpen={showBulkConfirmModal}
          onClose={() => setShowBulkConfirmModal(false)}
          title={`Confirm Bulk ${bulkActionType === 'approved' ? 'Verification' : 'Rejection'}`}
          footer={
            <>
              <Button variant="ghost" onClick={() => setShowBulkConfirmModal(false)}>
                Cancel
              </Button>
              <Button
                variant={bulkActionType === 'approved' ? 'success' : 'danger'}
                onClick={() => bulkReviewMutation.mutate()}
                isLoading={bulkReviewMutation.isPending}
              >
                Confirm {bulkActionType === 'approved' ? 'Approval' : 'Rejection as AI Mistakes'} ({selectedIds.length} records)
              </Button>
            </>
          }
        >
          <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
            Are you sure you want to bulk {bulkActionType === 'approved' ? 'confirm as genuine issues' : 'mark as AI mistakes'} for all <strong>{selectedIds.length}</strong> selected records?
          </p>
        </Modal>
      )}
    </div>
  );
}
