import { create } from 'zustand';
import { authApi } from '@/api/axios';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated';
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  initializeAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  status: 'idle',

  login: async (username: string, password: string) => {
    try {
      set({ status: 'loading' });

      const response = await authApi.post('/auth/login', {
        username,
        password,
      });

      const { access_token, refresh_token, user } = response.data;

      // Store tokens in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        user,
        status: 'authenticated',
      });
    } catch (error) {
      set({ status: 'unauthenticated' });
      throw error;
    }
  },

  logout: () => {
    // Clear tokens from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      status: 'unauthenticated',
    });
  },

  initializeAuth: () => {
    // Check for existing tokens in localStorage
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (accessToken && refreshToken) {
      set({
        accessToken,
        refreshToken,
        status: 'authenticated',
      });

      // Optionally fetch user profile
      authApi
        .get('/auth/me')
        .then((response) => {
          set({ user: response.data });
        })
        .catch(() => {
          // If token is invalid, logout
          useAuthStore.getState().logout();
        });
    } else {
      set({ status: 'unauthenticated' });
    }
  },
}));
