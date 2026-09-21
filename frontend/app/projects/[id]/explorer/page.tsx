'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  RotateCcw,
  ExternalLink,
  Eye,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { api } from '@/lib/api';
import { SourceRecord } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { Pagination } from '@/components/ui/Pagination';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';

export default function DataExplorerPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Read URL query parameters
  const page = parseInt(searchParams.get('page') || '1', 10);
  const platform = searchParams.get('platform') || '';
  const isDuplicate = searchParams.get('is_duplicate');
  const language = searchParams.get('language') || '';
  const search = searchParams.get('search') || '';
  const startDate = searchParams.get('start_date') || '';
  const endDate = searchParams.get('end_date') || '';

  const [searchInput, setSearchInput] = useState(search);
  const [selectedRecord, setSelectedRecord] = useState<SourceRecord | null>(null);

  // Sync state when URL updates
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
    // Reset to page 1 on filter changes unless page itself is changing
    if (!('page' in updates)) {
      current.set('page', '1');
    }
    router.push(`${pathname}?${current.toString()}`);
  };

  const clearAllFilters = () => {
    router.push(pathname);
    setSearchInput('');
  };

  const activeFiltersCount = [
    platform,
    isDuplicate,
    language,
    search,
    startDate,
    endDate,
  ].filter(Boolean).length;

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: [
      'source-records',
      projectId,
      page,
      platform,
      isDuplicate,
      language,
      search,
      startDate,
      endDate,
    ],
    queryFn: () =>
      api.getSourceRecords(projectId, {
        page,
        page_size: 50,
        platform: platform || undefined,
        is_duplicate: isDuplicate === 'true' ? true : isDuplicate === 'false' ? false : undefined,
        language: language || undefined,
        search: search || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      }),
    enabled: !!projectId,
    placeholderData: (prev) => prev,
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilters({ search: searchInput.trim() || null });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Filter Bar */}
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
            onSubmit={handleSearchSubmit}
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
                placeholder="Search raw feedback contents..."
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

          {/* Active filter count & clear */}
          {activeFiltersCount > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Badge variant="warning">{activeFiltersCount} active filter(s)</Badge>
              <Button size="sm" variant="ghost" onClick={clearAllFilters} leftIcon={<RotateCcw size={14} />}>
                Clear All
              </Button>
            </div>
          )}
        </div>

        {/* Dropdown Filters Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Platform Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Platform:</span>
            <select
              value={platform}
              onChange={(e) => updateFilters({ platform: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All Platforms</option>
              <option value="play_store">Google Play Store</option>
              <option value="app_store">Apple App Store</option>
              <option value="reddit">Reddit</option>
              <option value="youtube">YouTube</option>
              <option value="forum">Support Forum</option>
              <option value="manual_import">Manual Import</option>
            </select>
          </div>

          {/* Duplicate Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Duplicates:</span>
            <select
              value={isDuplicate || ''}
              onChange={(e) => updateFilters({ is_duplicate: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All Records</option>
              <option value="false">Unique Records Only</option>
              <option value="true">Exact Duplicates Only</option>
            </select>
          </div>

          {/* Language Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Language:</span>
            <select
              value={language}
              onChange={(e) => updateFilters({ language: e.target.value || null })}
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All Languages</option>
              <option value="en">English (en)</option>
              <option value="es">Spanish (es)</option>
              <option value="de">German (de)</option>
              <option value="fr">French (fr)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {isLoading ? (
          <Spinner size="lg" label="Loading source records..." style={{ minHeight: '300px' }} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No Matching Records Found"
            description="Try widening your search terms or resetting platform filters to inspect more source items."
            actionLabel="Reset Filters"
            onAction={clearAllFilters}
          />
        ) : (
          <div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>PLATFORM</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>AUTHOR / PSEUDONYM</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', width: '45%' }}>CONTENT PREVIEW</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>DATE</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>DUPLICATE</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'right' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((record) => (
                    <tr
                      key={record.id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background var(--transition-fast)',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '0.85rem 1rem', whiteSpace: 'nowrap' }}>
                        <SourceBadge platform={record.source_platform} size="sm" />
                      </td>
                      <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {record.author_handle || 'anonymous'}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                        <div style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                          {record.raw_content}
                        </div>
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-muted)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                        {record.source_date ? new Date(record.source_date).toLocaleDateString() : 'N/A'}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {record.is_duplicate ? (
                          <Badge variant="warning" size="sm">Duplicate</Badge>
                        ) : (
                          <Badge variant="neutral" size="sm">Unique</Badge>
                        )}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedRecord(record)}
                            leftIcon={<Eye size={13} />}
                          >
                            Inspect
                          </Button>
                          <Link href={`/projects/${projectId}/evidence?search=${encodeURIComponent(record.raw_content.substring(0, 40))}`}>
                            <Button size="sm" variant="ghost" title="Search evidence for this record">
                              <ExternalLink size={13} />
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Server Pagination */}
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
      </div>

      {/* Record Inspect Modal */}
      {selectedRecord && (
        <Modal
          isOpen={!!selectedRecord}
          onClose={() => setSelectedRecord(null)}
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <SourceBadge platform={selectedRecord.source_platform} />
              <span>Source Record Details</span>
            </div>
          }
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Author ID: {selectedRecord.author_handle} (Pseudonymized)
              </div>
              <Button variant="primary" onClick={() => setSelectedRecord(null)}>
                Close
              </Button>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                RAW UNALTERED FEEDBACK
              </div>
              <div
                style={{
                  padding: '1rem',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {selectedRecord.raw_content}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Collection Method</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 500, marginTop: '0.2rem' }}>
                  {selectedRecord.collection_method}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Published Date</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 500, marginTop: '0.2rem' }}>
                  {selectedRecord.source_date ? new Date(selectedRecord.source_date).toLocaleString() : 'N/A'}
                </div>
              </div>
              {selectedRecord.source_url && (
                <div style={{ gridColumn: 'span 2' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Source Link</span>
                  <div style={{ fontSize: '0.85rem', marginTop: '0.2rem', wordBreak: 'break-all' }}>
                    <a
                      href={selectedRecord.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--google-blue)', textDecoration: 'underline' }}
                    >
                      {selectedRecord.source_url}
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
