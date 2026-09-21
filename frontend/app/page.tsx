'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth-store';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/projects');
    } else {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <div style={{ textAlign: 'center' }}>
        <div className="badge badge-info" style={{ marginBottom: '1rem' }}>
          Loading Discovery Engine...
        </div>
      </div>
    </div>
  );
}
