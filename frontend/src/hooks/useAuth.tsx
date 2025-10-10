/**
 * Authentication context and hooks.
 *
 * Provides JWT token management with localStorage persistence
 * and automatic token refresh.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User, AuthState } from '../types/auth';

interface AuthContextType extends AuthState {
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Token storage keys.
 */
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

/**
 * Authentication provider component.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  /**
   * Initialize auth state from localStorage on mount.
   */
  useEffect(() => {
    const initAuth = () => {
      try {
        const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
        const userStr = localStorage.getItem(USER_KEY);

        if (accessToken && userStr) {
          const user = JSON.parse(userStr);
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } else {
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);

  /**
   * Login: Store tokens and user in localStorage.
   */
  const login = (accessToken: string, refreshToken: string, user: User) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({
      user,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  /**
   * Logout: Clear tokens and user from localStorage.
   */
  const logout = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  /**
   * Update user data.
   */
  const updateUser = (user: User) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState((prev) => ({
      ...prev,
      user,
    }));
  };

  /**
   * Get access token from localStorage.
   */
  const getAccessToken = (): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  };

  /**
   * Get refresh token from localStorage.
   */
  const getRefreshToken = (): string | null => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    updateUser,
    getAccessToken,
    getRefreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to use authentication context.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
