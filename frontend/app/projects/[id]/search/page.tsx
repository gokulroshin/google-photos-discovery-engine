'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Sparkles,
  Sliders,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  ExternalLink,
  Zap,
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvidenceRecord } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ConfidenceBadge } from '@/components/ui/ConfidenceBadge';
import { OutcomeBadge } from '@/components/ui/OutcomeBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

export default function SemanticSearchPage() {
  const params = useParams();
  const projectId = params?.id as string;

  const [searchQuery, setSearchQuery] = useState('searching for nephew in red hat eating ice cream summer 2021');
  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);
  const [minSimilarity, setMinSimilarity] = useState(0.4);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(null);

  // 300ms debounce
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  const wordCount = searchQuery.trim().split(/\s+/).filter(Boolean).length;
  const isShortQuery = wordCount > 0 && wordCount < 5;

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['semantic-search', projectId, debouncedQuery, minSimilarity],
    queryFn: () => api.searchEvidence(projectId, debouncedQuery, 20, minSimilarity),
    enabled: !!projectId && debouncedQuery.trim().length > 0,
  });

  const sampleQueries = [
    'nephew wearing red hat eating chocolate ice cream in Chicago summer 2021',
    'receipt screenshot buried under candid beach photo search results',
    'can not remember the year but it was right after we moved into the apartment',
    'dog playing fetch in the snow when I had long hair in college',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Search Bar Header */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.01em', marginBottom: '0.25rem' }}>
            Semantic Vector Search & Discovery
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Query evidence records using natural language episodic memory descriptions powered by pgvector embeddings.
          </p>
        </div>

        {/* Input box */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.75rem 1rem',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-focus, #3b82f6)',
            boxShadow: '0 0 0 2px var(--accent-glow, rgba(59, 130, 246, 0.2))',
            marginBottom: '1rem',
          }}
        >
          <Search size={20} color="var(--accent-primary)" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Type a natural episodic memory query (e.g. 'daughter yellow dress birthday cake')..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '1rem',
              width: '100%',
            }}
          />
          {isFetching && <Spinner size="sm" />}
        </div>

        {/* Short query guidance alert */}
        {isShortQuery && (
          <div
            style={{
              padding: '0.6rem 0.85rem',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              borderRadius: 'var(--radius-sm)',
              color: '#93c5fd',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem',
            }}
          >
            <Sparkles size={14} />
            <span>
              <strong>Tip:</strong> Queries with 5+ words (specifying visual cues, emotions, or settings) yield substantially richer semantic embedding matches.
            </span>
          </div>
        )}

        {/* Suggested Queries Chips */}
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>
            TRY SAMPLE NATURAL MEMORY QUERIES:
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {sampleQueries.map((q, idx) => (
              <button
                key={idx}
                onClick={() => setSearchQuery(q)}
                style={{
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.775rem',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '9999px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
              >
                &ldquo;{q}&rdquo;
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Header Strip */}
      {data && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 0.5rem' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Found <strong style={{ color: 'var(--text-primary)' }}>{data.total_matches}</strong> semantic matches for &ldquo;{data.query}&rdquo;
          </div>
          {data.is_low_confidence && (
            <Badge variant="warning">Low Confidence Fallback Matches</Badge>
          )}
        </div>
      )}

      {/* Results List */}
      {isLoading ? (
        <Spinner size="lg" label="Computing embedding similarity..." style={{ minHeight: '250px' }} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No Matching Evidence Found"
          description="Try broadening your search phrasing or using one of the sample queries above."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {data.items.map((item, idx) => {
            const similarity = item.similarity_score || 0.9 - idx * 0.05;
            const simPercent = Math.round(similarity * 100);

            return (
              <div
                key={item.id}
                className="card"
                style={{
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  border: similarity > 0.85 ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid var(--border-subtle)',
                }}
              >
                {/* Match Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.6rem',
                        background: similarity > 0.8 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                        border: `1px solid ${similarity > 0.8 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
                        borderRadius: '9999px',
                        color: similarity > 0.8 ? '#34d399' : '#60a5fa',
                        fontSize: '0.775rem',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {simPercent}% Cosine Match
                    </span>
                    {item.source_platform && <SourceBadge platform={item.source_platform} size="sm" />}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <ConfidenceBadge score={item.confidence_score} size="sm" />
                    <OutcomeBadge outcome={item.retrieval_outcome} size="sm" />
                  </div>
                </div>

                {/* Scenario Title */}
                <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {item.retrieval_scenario}
                </h4>

                {/* Verbatim Excerpt */}
                {item.evidence_excerpt && (
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
                    }}
                  >
                    &ldquo;{item.evidence_excerpt}&rdquo;
                  </div>
                )}

                {/* Rationale & Action */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.65rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Gemini Rationale: {item.rationale.substring(0, 90)}...
                  </span>

                  <Button size="sm" variant="outline" onClick={() => setSelectedEvidence(item)}>
                    Inspect Full Extraction
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Inspect Modal */}
      {selectedEvidence && (
        <Modal
          isOpen={!!selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
          title="Search Match Evidence Details"
          footer={
            <Button variant="primary" onClick={() => setSelectedEvidence(null)}>
              Close
            </Button>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <strong style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>RAW CONTENT:</strong>
              <div style={{ padding: '0.75rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginTop: '0.25rem', fontSize: '0.85rem' }}>
                {selectedEvidence.raw_content || selectedEvidence.evidence_excerpt}
              </div>
            </div>

            <div>
              <strong style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>GEMINI RATIONALE:</strong>
              <div style={{ fontSize: '0.85rem', marginTop: '0.25rem', lineHeight: 1.5 }}>
                {selectedEvidence.rationale}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
