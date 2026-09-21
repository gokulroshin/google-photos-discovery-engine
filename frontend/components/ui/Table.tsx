import React from 'react';

export interface TableProps {
  headers: string[];
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const Table: React.FC<TableProps> = ({ headers, children, style }) => {
  return (
    <div
      style={{
        width: '100%',
        overflowX: 'auto',
        background: 'var(--bg-secondary, #111827)',
        borderRadius: 'var(--radius-md, 10px)',
        border: '1px solid var(--border-subtle)',
        ...style,
      }}
    >
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          textAlign: 'left',
          fontSize: '0.875rem',
        }}
      >
        <thead>
          <tr
            style={{
              background: 'var(--bg-surface-elevated, #1a2234)',
              borderBottom: '1px solid var(--border-subtle)',
            }}
          >
            {headers.map((header, idx) => (
              <th
                key={idx}
                style={{
                  padding: '0.85rem 1rem',
                  fontWeight: 600,
                  fontSize: '0.775rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-secondary)',
                  whiteSpace: 'nowrap',
                }}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
};
