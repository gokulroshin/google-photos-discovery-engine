'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/projects/proj_photo_retrieval_2026/taxonomy');
  }, [router]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <div style={{ textAlign: 'center' }}>
        <div className="badge badge-info" style={{ marginBottom: '1rem', padding: '0.6rem 1.2rem', fontSize: '0.9rem' }}>
          Opening Google Photos Discovery Engine...
        </div>
      </div>
    </div>
  );
}
