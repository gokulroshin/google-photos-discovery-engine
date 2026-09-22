'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/projects');
  }, [router]);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 4rem)',
        padding: '1rem',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div className="badge badge-info" style={{ padding: '0.75rem 1.5rem', fontSize: '0.9rem' }}>
          Redirecting to Discovery Workspace...
        </div>
      </div>
    </div>
  );
}
