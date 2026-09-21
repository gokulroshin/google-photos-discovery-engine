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
        reviewer_notes: 'Bulk approved by researcher',
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
    if (!data?.items) return;
    if (selectedIds.length === data.items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(data.items.map((i) => i.id));
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

  const isAllSelected = data?.items && data.items.length > 0 && selectedIds.length === data.items.length;

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
              Human Review & Verification Queue
            </h2>
            <Badge variant="warning">
              {data?.total || 0} Records Pending Review
            </Badge>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Low confidence AI extractions (&lt; 0.70) flagged for researcher verification to eliminate hallucination risk.
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
              Bulk Approve Selected
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
              Bulk Reject Selected
            </Button>
          </div>
        )}
      </div>

      {isLoading ? (
        <Spinner size="lg" label="Loading review queue..." style={{ minHeight: '300px' }} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 size={32} color="#10b981" />}
          title="Review Queue is Clean"
          description="All extracted evidence records have either met the high confidence threshold (≥ 0.70) or been verified by researchers."
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
              <span>Select All on Page</span>
            </button>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Sorted by Lowest Confidence First
            </span>
          </div>

          {/* Queue Items */}
          {data.items.map((record) => {
            const isSelected = selectedIds.includes(record.id);

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
                    : '1px solid rgba(245, 158, 11, 0.3)',
                  background: isSelected ? 'rgba(66, 133, 244, 0.05)' : undefined,
                }}
              >
                {/* Item Top Bar */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <button
                      onClick={() => handleToggleSelect(record.id)}
                      style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
                    >
                      {isSelected ? <CheckSquare size={18} color="var(--google-blue)" /> : <Square size={18} />}
                    </button>
                    <ConfidenceBadge score={record.confidence_score} />
                    <OutcomeBadge outcome={record.retrieval_outcome} size="sm" />
                    {record.source_platform && <SourceBadge platform={record.source_platform} size="sm" />}
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Button
                      size="sm"
                      variant="success"
                      onClick={() => singleReviewMutation.mutate({ id: record.id, action: 'approved' })}
                      isLoading={singleReviewMutation.isPending}
                      leftIcon={<CheckCircle2 size={13} />}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenCorrect(record)}
                      leftIcon={<Edit3 size={13} />}
                    >
                      Correct
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => singleReviewMutation.mutate({ id: record.id, action: 'rejected' })}
                      isLoading={singleReviewMutation.isPending}
                      leftIcon={<XCircle size={13} />}
                    >
                      Reject
                    </Button>
                  </div>
                </div>

                {/* Scenario & Rationale */}
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                    Scenario: {record.retrieval_scenario}
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
                    <strong>Gemini Extraction Rationale:</strong> {record.rationale}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Pagination */}
          <Pagination
            currentPage={data.page}
            totalPages={data.total_pages}
            totalItems={data.total}
            pageSize={data.page_size}
            onPageChange={(p) => setPage(p)}
          />
        </div>
      )}

      {/* Correct / Edit Modal */}
      {editingRecord && (
        <Modal
          isOpen={!!editingRecord}
          onClose={() => setEditingRecord(null)}
          title="Correct AI Classification Fields"
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
                Submit Corrections
              </Button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Retrieval Scenario Description
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
                Retrieval Outcome
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
                <option value="gave_up">Gave Up / Abandoned</option>
                <option value="found_after_effort">Found After Effort</option>
                <option value="never_found">Never Found</option>
                <option value="found_alternative">Workaround / Alternative</option>
                <option value="found_quickly">Found Quickly</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Reviewer Rationale & Notes
              </label>
              <textarea
                rows={3}
                value={notesInput}
                onChange={(e) => setNotesInput(e.target.value)}
                placeholder="Explain the correction rationale for audit logs..."
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
          title={`Confirm Bulk ${bulkActionType.toUpperCase()}`}
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
                Confirm {bulkActionType === 'approved' ? 'Approval' : 'Rejection'} ({selectedIds.length} records)
              </Button>
            </>
          }
        >
          <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
            Are you sure you want to bulk {bulkActionType} all <strong>{selectedIds.length}</strong> selected records?
          </p>
        </Modal>
      )}
    </div>
  );
}
