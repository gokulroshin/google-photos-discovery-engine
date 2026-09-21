'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Layers,
  Sparkles,
  Users,
  Database,
  ExternalLink,
  Edit3,
  AlertTriangle,
  HelpCircle,
  Lightbulb,
  ArrowRight,
  Sliders,
} from 'lucide-react';
import { api } from '@/lib/api';
import { TaxonomyCategory } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

export default function TaxonomyPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const queryClient = useQueryClient();

  const [selectedCategory, setSelectedCategory] = useState<TaxonomyCategory | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [clustersK, setClustersK] = useState(8);
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>(undefined);

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDefinition, setEditDefinition] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['taxonomy', projectId, selectedVersion],
    queryFn: () => api.getTaxonomy(projectId, selectedVersion),
    enabled: !!projectId,
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateTaxonomy(projectId, clustersK),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['taxonomy', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] });
      setShowGenerateModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!selectedCategory) throw new Error('No category selected');
      return api.updateTaxonomyCategory(projectId, selectedCategory.id, {
        name: editName,
        definition: editDefinition,
      });
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['taxonomy', projectId] });
      setSelectedCategory(updated);
      setIsEditing(false);
    },
  });

  const handleOpenEdit = (cat: TaxonomyCategory) => {
    setSelectedCategory(cat);
    setEditName(cat.name);
    setEditDefinition(cat.definition);
    setIsEditing(true);
  };

  const categories = data?.categories || [];
  const potentialDuplicates = data?.potential_duplicates || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Action Bar */}
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
            Retrieval Problem Taxonomy
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Empirically grounded failure categories synthesized from clustered user evidence.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {data?.latest_version && data.latest_version > 1 && (
            <select
              value={selectedVersion || data.latest_version}
              onChange={(e) => setSelectedVersion(Number(e.target.value))}
              style={{
                padding: '0.45rem 0.75rem',
                fontSize: '0.825rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
              }}
            >
              {Array.from({ length: data.latest_version }).map((_, i) => (
                <option key={i + 1} value={i + 1}>
                  Taxonomy Version {i + 1}
                </option>
              ))}
            </select>
          )}

          <Button
            variant="primary"
            onClick={() => setShowGenerateModal(true)}
            leftIcon={<Sparkles size={16} />}
          >
            Generate Taxonomy
          </Button>
        </div>
      </div>

      {/* Potential Duplicate Categories Warning */}
      {potentialDuplicates.length > 0 && (
        <Alert
          variant="warning"
          title="Potential Duplicate Problem Categories Detected"
        >
          {potentialDuplicates.length} category pair(s) exhibit pairwise semantic similarity &gt; 0.85. Review and consider merging overlapping clusters.
        </Alert>
      )}

      {/* Category Cards Grid */}
      {isLoading ? (
        <Spinner size="lg" label="Clustering and synthesizing taxonomy..." style={{ minHeight: '300px' }} />
      ) : categories.length === 0 ? (
        <EmptyState
          title="No Taxonomy Generated Yet"
          description="Taxonomy clustering groups verified user evidence by failure mechanisms and memory cues."
          actionLabel="Run Semantic Clustering & Synthesis"
          onAction={() => setShowGenerateModal(true)}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {categories.map((cat) => (
            <div
              key={cat.id}
              className="card"
              style={{
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1.25rem',
                transition: 'transform var(--transition-fast)',
              }}
            >
              <div>
                {/* Header: Confidence & Evidence Count */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '0.75rem',
                  }}
                >
                  <Badge
                    variant={
                      cat.confidence_level === 'high'
                        ? 'success'
                        : cat.confidence_level === 'medium'
                        ? 'info'
                        : 'warning'
                    }
                  >
                    {cat.confidence_level.toUpperCase()} CONFIDENCE
                  </Badge>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Database size={13} /> {cat.evidence_count} evidence
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Users size={13} /> {cat.unique_author_count} authors
                    </span>
                  </div>
                </div>

                {/* Category Title */}
                <h3
                  style={{
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '0.6rem',
                    lineHeight: 1.35,
                  }}
                >
                  {cat.name}
                </h3>

                {/* Definition Summary */}
                <p
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.55,
                    marginBottom: '1rem',
                  }}
                >
                  {cat.definition}
                </p>

                {/* Source Diversity Pills */}
                {cat.source_diversity && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
                    {Object.entries(cat.source_diversity).map(([platform, count]) => (
                      <span
                        key={platform}
                        style={{
                          fontSize: '0.7rem',
                          padding: '0.15rem 0.5rem',
                          background: 'rgba(255, 255, 255, 0.05)',
                          borderRadius: '9999px',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {platform.replace('_', ' ')}: <strong>{count}</strong>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '0.85rem',
                }}
              >
                <Link
                  href={`/projects/${projectId}/evidence?scenario=${encodeURIComponent(cat.name)}`}
                  style={{
                    fontSize: '0.8rem',
                    color: 'var(--google-blue)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                  }}
                >
                  View Evidence ({cat.evidence_count}) <ArrowRight size={13} />
                </Link>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedCategory(cat)}
                  leftIcon={<Layers size={13} />}
                >
                  Explore Category
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Category Deep-Dive Modal */}
      {selectedCategory && (
        <Modal
          isOpen={!!selectedCategory}
          onClose={() => {
            setSelectedCategory(null);
            setIsEditing(false);
          }}
          maxWidth="780px"
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Layers size={18} color="var(--accent-primary)" />
              <span>{isEditing ? 'Edit Category Definition' : selectedCategory.name}</span>
            </div>
          }
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              {!isEditing ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleOpenEdit(selectedCategory)}
                  leftIcon={<Edit3 size={14} />}
                >
                  Edit Category
                </Button>
              ) : (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button size="sm" variant="ghost" onClick={() => setIsEditing(false)}>
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => updateMutation.mutate()}
                    isLoading={updateMutation.isPending}
                  >
                    Save Changes
                  </Button>
                </div>
              )}
              <Button
                variant="primary"
                onClick={() => {
                  setSelectedCategory(null);
                  setIsEditing(false);
                }}
              >
                Done
              </Button>
            </div>
          }
        >
          {isEditing ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Category Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.9rem',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Category Definition & Scope
                </label>
                <textarea
                  rows={4}
                  value={editDefinition}
                  onChange={(e) => setEditDefinition(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.9rem',
                    lineHeight: 1.5,
                  }}
                />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Definition */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  DEFINITION & SCOPE
                </div>
                <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
                  {selectedCategory.definition}
                </p>
              </div>

              {/* Mechanism & User Segment */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ padding: '0.85rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    FAILURE MECHANISM
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {selectedCategory.failure_mechanism}
                  </div>
                </div>

                <div style={{ padding: '0.85rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    TARGET USER SEGMENT
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {selectedCategory.user_segment}
                  </div>
                </div>
              </div>

              {/* Representative Verbatim Quotes */}
              {selectedCategory.representative_excerpts && selectedCategory.representative_excerpts.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                    REPRESENTATIVE USER EXCERPTS ({selectedCategory.representative_excerpts.length})
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {selectedCategory.representative_excerpts.map((excerpt, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '0.75rem 1rem',
                          background: 'rgba(255, 255, 255, 0.03)',
                          borderLeft: '3px solid var(--google-yellow, #fbbc05)',
                          borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                          fontSize: '0.85rem',
                          fontStyle: 'italic',
                          color: '#fef08a',
                          lineHeight: 1.5,
                        }}
                      >
                        &ldquo;{excerpt}&rdquo;
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Product Implications */}
              {selectedCategory.product_implications && (
                <div style={{ padding: '0.85rem', background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', fontWeight: 600, color: '#60a5fa', marginBottom: '0.25rem' }}>
                    <Lightbulb size={14} /> PRODUCT IMPLICATIONS FOR GOOGLE PHOTOS
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                    {selectedCategory.product_implications}
                  </div>
                </div>
              )}
            </div>
          )}
        </Modal>
      )}

      {/* Generate Taxonomy Modal */}
      <Modal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        title="Run Semantic Taxonomy Generation"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowGenerateModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => generateMutation.mutate()}
              isLoading={generateMutation.isPending}
              leftIcon={<Sparkles size={16} />}
            >
              Generate Taxonomy Clusters
            </Button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Semantic clustering executes pgvector cosine similarity grouping over all relevant evidence records, then invokes Gemini with representative samples to synthesize grounded category definitions.
          </p>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                Target Number of Clusters (k): {clustersK}
              </label>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Range: 3–15</span>
            </div>
            <input
              type="range"
              min={3}
              max={15}
              value={clustersK}
              onChange={(e) => setClustersK(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--google-blue)' }}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
