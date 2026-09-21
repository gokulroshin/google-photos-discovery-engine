import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button } from './Button';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  isLoading = false,
}) => {
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.85rem 1rem',
        background: 'var(--bg-surface-elevated, #1a2234)',
        borderTop: '1px solid var(--border-subtle)',
        flexWrap: 'wrap',
        gap: '1rem',
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
      }}
    >
      <div>
        Showing{' '}
        <strong style={{ color: 'var(--text-primary)' }}>
          {startItem}–{endItem}
        </strong>{' '}
        of <strong style={{ color: 'var(--text-primary)' }}>{totalItems}</strong> records
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <Button
          size="sm"
          variant="outline"
          disabled={currentPage <= 1 || isLoading}
          onClick={() => onPageChange(1)}
          title="First Page"
        >
          <ChevronsLeft size={16} />
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={currentPage <= 1 || isLoading}
          onClick={() => onPageChange(currentPage - 1)}
          title="Previous Page"
        >
          <ChevronLeft size={16} />
        </Button>

        <span
          style={{
            padding: '0.35rem 0.75rem',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md, 8px)',
            fontSize: '0.8125rem',
            color: 'var(--text-primary)',
            fontWeight: 500,
          }}
        >
          Page {currentPage} of {Math.max(1, totalPages)}
        </span>

        <Button
          size="sm"
          variant="outline"
          disabled={currentPage >= totalPages || isLoading}
          onClick={() => onPageChange(currentPage + 1)}
          title="Next Page"
        >
          <ChevronRight size={16} />
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={currentPage >= totalPages || isLoading}
          onClick={() => onPageChange(totalPages)}
          title="Last Page"
        >
          <ChevronsRight size={16} />
        </Button>
      </div>
    </div>
  );
};
