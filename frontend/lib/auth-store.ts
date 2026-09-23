import { create } from 'zustand';
import { User } from './types';

const DEFAULT_PUBLIC_USER: User = {
  id: 'usr_public_admin',
  email: 'public@google-photos.discovery',
  name: 'Public Researcher',
  role: 'admin',
};

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeProjectId: string | null;
  setUser: (user: User | null, token?: string | null) => void;
  setActiveProjectId: (id: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: DEFAULT_PUBLIC_USER,
  token: typeof window !== 'undefined' ? localStorage.getItem('auth_token') || 'public_access_token' : 'public_access_token',
  isAuthenticated: true,
  isLoading: false,
  activeProjectId: 'proj_photo_retrieval_2026',
  setUser: (user, token) => {
    const finalUser = user || DEFAULT_PUBLIC_USER;
    if (typeof window !== 'undefined') {
      if (token) localStorage.setItem('auth_token', token);
    }
    set({ user: finalUser, token: token || 'public_access_token', isAuthenticated: true });
  },
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  logout: () => {
    set({ user: DEFAULT_PUBLIC_USER, token: 'public_access_token', isAuthenticated: true });
  },
}));
