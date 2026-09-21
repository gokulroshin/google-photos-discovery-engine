'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BarChart3,
  Sparkles,
  Download,
  Edit3,
  Sliders,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react';
import { api } from '@/lib/api';
import { OpportunityArea } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import { Tooltip } from '@/components/ui/Tooltip';

interface DimensionConfig {
  key: keyof OpportunityArea;
  label: string;
  description: string;
  type: 'score' | 'percent' | 'badge' | 'text';
}

const ALL_DIMENSIONS: DimensionConfig[] = [
  {
    key: 'evidence_frequency',
    label: 'Evidence Frequency',
    description: 'Number of verified evidence records mapped to this problem area',
    type: 'score',
  },
  {
    key: 'user_impact_score',
    label: 'User Impact Score (0–10)',
    description: 'Estimated severity of user frustration and task impediment',
    type: 'score',
  },
  {
    key: 'abandonment_rate',
    label: 'Search Abandonment Rate',
    description: 'Proportion of users who gave up on finding their photo',
    type: 'percent',
  },
  {
    key: 'strategic_relevance',
    label: 'Strategic Relevance (0–10)',
    description: 'Alignment with Google Photos AI retrieval and core product vision',
    type: 'score',
  },
  {
    key: 'problem_clarity',
    label: 'Problem Clarity (0–10)',
    description: 'Precision of the root cause mechanism based on user testimonies',
    type: 'score',
  },
  {
    key: 'potential_reach',
    label: 'Potential Reach',
    description: 'Breadth of the user population affected by this failure',
    type: 'text',
  },
  {
    key: 'validation_effort',
    label: 'Validation Effort',
    description: 'Technical and researcher effort required to prototype and test solution',
    type: 'badge',
  },
  {
    key: 'workaround_exists',
    label: 'Workaround Exists',
    description: 'Whether users currently adopt manual tricks or third-party apps',
    type: 'text',
  },
];

export default function OpportunityComparisonPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const queryClient = useQueryClient();

  const [visibleDims, setVisibleDims] = useState<string[]>(ALL_DIMENSIONS.map((d) => d.key as string));
  const [selectedCell, setSelectedCell] = useState<{ opp: OpportunityArea; dim: DimensionConfig } | null>(null);
  const [editingOpp, setEditingOpp] = useState<OpportunityArea | null>(null);
  const [overrideNotes, setOverrideNotes] = useState('');
  const [impactScore, setImpactScore] = useState<number>(8);

  const { data: opportunities, isLoading } = useQuery({
    queryKey: ['opportunities', projectId],
    queryFn: () => api.getOpportunities(projectId),
    enabled: !!projectId,
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateOpportunities(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editingOpp) throw new Error('No opportunity selected');
      if (!overrideNotes.trim()) throw new Error('Analyst override notes are required for score adjustments.');
      return api.updateOpportunity(projectId, editingOpp.id, {
        user_impact_score: impactScore,
        analyst_notes: overrideNotes,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities', projectId] });
      setEditingOpp(null);
    },
  });

  const validatedOpps = (opportunities || []).filter((o) => o.status !== 'speculative');
  const speculativeOpps = (opportunities || []).filter((o) => o.status === 'speculative');

  // Heatmap background calculation for scores
  const getCellBackground = (val: any, type: string) => {
    if (type === 'score' && typeof val === 'number') {
      if (val >= 8.5) return 'rgba(16, 185, 129, 0.2)'; // Green
      if (val >= 7.0) return 'rgba(59, 130, 246, 0.18)'; // Blue
      if (val >= 5.0) return 'rgba(245, 158, 11, 0.18)'; // Amber
      return 'rgba(239, 68, 68, 0.15)'; // Red
    }
    if (type === 'percent' && typeof val === 'number') {
      if (val >= 0.6) return 'rgba(239, 68, 68, 0.2)'; // High abandonment
      if (val >= 0.3) return 'rgba(245, 158, 11, 0.18)';
      return 'rgba(16, 185, 129, 0.18)';
    }
    return 'transparent';
  };

  const exportCSV = () => {
    if (!opportunities || opportunities.length === 0) return;
    const headers = ['Opportunity Name', 'Status', ...ALL_DIMENSIONS.map((d) => d.label)];
    const rows = opportunities.map((opp) => [
      `"${opp.name.replace(/"/g, '""')}"`,
      opp.status,
      ...ALL_DIMENSIONS.map((d) => {
        const val = opp[d.key];
        return typeof val === 'object' ? `"${JSON.stringify(val)}"` : `"${val}"`;
      }),
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `opportunity_comparison_${projectId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Action Header */}
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
            Opportunity Area Comparison Matrix
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Multi-dimensional evaluation across 9 objective metrics to prioritize photo retrieval investments.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={exportCSV}
            leftIcon={<Download size={14} />}
            disabled={!opportunities || opportunities.length === 0}
          >
            Export CSV
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => generateMutation.mutate()}
            isLoading={generateMutation.isPending}
            leftIcon={<Sparkles size={14} />}
          >
            Re-score Opportunities
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Spinner size="lg" label="Evaluating opportunity areas..." style={{ minHeight: '300px' }} />
      ) : !opportunities || opportunities.length === 0 ? (
        <EmptyState
          title="No Opportunity Areas Generated"
          description="Opportunity areas are synthesized by scoring taxonomy problem clusters on strategic fit, user impact, and evidence volume."
          actionLabel="Generate Opportunity Areas"
          onAction={() => generateMutation.mutate()}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Heatmap Matrix Table */}
          <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '800px' }}>
              <thead>
                <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th
                    style={{
                      padding: '1rem 1.25rem',
                      width: '260px',
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                      position: 'sticky',
                      left: 0,
                      background: 'var(--bg-surface-elevated)',
                      zIndex: 2,
                    }}
                  >
                    EVALUATION DIMENSION
                  </th>
                  {validatedOpps.map((opp) => (
                    <th
                      key={opp.id}
                      style={{
                        padding: '1rem 1.25rem',
                        fontSize: '0.875rem',
                        color: 'var(--text-primary)',
                        minWidth: '220px',
                        borderLeft: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 700 }}>{opp.name}</span>
                        <button
                          onClick={() => {
                            setEditingOpp(opp);
                            setImpactScore(opp.user_impact_score);
                            setOverrideNotes(opp.analyst_notes || '');
                          }}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                          }}
                          title="Override scores or add analyst notes"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ALL_DIMENSIONS.filter((d) => visibleDims.includes(d.key as string)).map((dim, idx) => (
                  <tr
                    key={dim.key}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                    }}
                  >
                    {/* Dimension Name Column */}
                    <td
                      style={{
                        padding: '0.9rem 1.25rem',
                        fontSize: '0.825rem',
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        position: 'sticky',
                        left: 0,
                        background: 'var(--bg-secondary)',
                        zIndex: 1,
                        borderRight: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <span>{dim.label}</span>
                        <Tooltip content={dim.description}>
                          <HelpCircle size={13} style={{ opacity: 0.5, cursor: 'help' }} />
                        </Tooltip>
                      </div>
                    </td>

                    {/* Matrix Cells */}
                    {validatedOpps.map((opp) => {
                      const val = opp[dim.key];
                      const bg = getCellBackground(val, dim.type);

                      return (
                        <td
                          key={opp.id}
                          onClick={() => setSelectedCell({ opp, dim })}
                          style={{
                            padding: '0.9rem 1.25rem',
                            fontSize: '0.875rem',
                            borderLeft: '1px solid var(--border-subtle)',
                            background: bg,
                            cursor: 'pointer',
                            transition: 'opacity var(--transition-fast)',
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.85')}
                          onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
                          title="Click to view scoring rationale and methodology"
                        >
                          {dim.type === 'score' && typeof val === 'number' && (
                            <strong style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>
                              {val.toFixed(1)}
                            </strong>
                          )}

                          {dim.type === 'percent' && typeof val === 'number' && (
                            <span style={{ fontWeight: 600, color: val > 0.5 ? '#f87171' : 'var(--text-primary)' }}>
                              {Math.round(val * 100)}%
                            </span>
                          )}

                          {dim.type === 'badge' && (
                            <Badge
                              variant={
                                val === 'low' ? 'success' : val === 'medium' ? 'warning' : 'danger'
                              }
                            >
                              {String(val).toUpperCase()}
                            </Badge>
                          )}

                          {dim.type === 'text' && (
                            <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                              {String(val)}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Speculative Opportunities Section */}
          {speculativeOpps.length > 0 && (
            <div className="card" style={{ padding: '1.5rem', border: '1px dashed rgba(245, 158, 11, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <AlertCircle size={18} color="var(--status-warning)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Speculative / Emerging Opportunities</h3>
                <Badge variant="warning">0 Verified Evidence Records</Badge>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                These candidate focus areas are hypothesized from market trends but currently lack direct empirical support in public feedback datasets.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                {speculativeOpps.map((opp) => (
                  <div
                    key={opp.id}
                    style={{
                      padding: '1rem',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.35rem' }}>
                      {opp.name}
                    </div>
                    <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {opp.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Cell Methodology & Evidence Modal */}
      {selectedCell && (
        <Modal
          isOpen={!!selectedCell}
          onClose={() => setSelectedCell(null)}
          title={`${selectedCell.opp.name} — ${selectedCell.dim.label}`}
          footer={
            <Button variant="primary" onClick={() => setSelectedCell(null)}>
              Close
            </Button>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                CURRENT METRIC VALUE
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {String(selectedCell.opp[selectedCell.dim.key])}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                SCORING METHODOLOGY & FORMULA
              </div>
              <div
                style={{
                  padding: '0.85rem',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  lineHeight: 1.5,
                  color: 'var(--text-primary)',
                }}
              >
                {selectedCell.opp.scoring_methodology ||
                  'Score synthesized by Gemini using multi-factor prompt scoring based on failure frequency and severity.'}
              </div>
            </div>

            {selectedCell.opp.analyst_notes && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  ANALYST OVERRIDE NOTES
                </div>
                <div
                  style={{
                    padding: '0.85rem',
                    background: 'rgba(59, 130, 246, 0.08)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.85rem',
                    color: '#93c5fd',
                  }}
                >
                  {selectedCell.opp.analyst_notes}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Analyst Score Override Modal */}
      {editingOpp && (
        <Modal
          isOpen={!!editingOpp}
          onClose={() => setEditingOpp(null)}
          title={`Override Score: ${editingOpp.name}`}
          footer={
            <>
              <Button variant="ghost" onClick={() => setEditingOpp(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => updateMutation.mutate()}
                isLoading={updateMutation.isPending}
              >
                Save Override
              </Button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                  Adjust User Impact Score (0–10): {impactScore}
                </label>
              </div>
              <input
                type="range"
                min={0}
                max={10}
                step={0.1}
                value={impactScore}
                onChange={(e) => setImpactScore(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--google-blue)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Mandatory Analyst Rationale / Notes *
              </label>
              <textarea
                rows={3}
                placeholder="Explain why this score was manually adjusted (e.g. alignment with upcoming Q3 model upgrades)..."
                value={overrideNotes}
                onChange={(e) => setOverrideNotes(e.target.value)}
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
    </div>
  );
}
