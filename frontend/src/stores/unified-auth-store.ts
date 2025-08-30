/**
 * WealthPath AI - Unified Authentication Store
 * CRITICAL: Single source of truth for ALL auth state
 * Uses sessionStorage for tab isolation, preventing hanging issues
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { User, UserProfile, AuthTokens } from '../types/auth';

interface UnifiedAuthState {
  user: User | null;
  profile: UserProfile | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface UnifiedAuthStore extends UnifiedAuthState {
  // Core actions
  setAuth: (tokens: AuthTokens, user: User, profile?: UserProfile) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Computed getters
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  isTokenExpired: () => boolean;
  getFullName: () => string;
  
  // Migration utilities
  migrateFromLegacy: () => void;
}

// Custom sessionStorage adapter for tab isolation
const SESSION_STORAGE_KEY = 'wpa-unified-auth';

const sessionStorageAdapter = {
  getItem: (name: string) => {
    try {
      const item = sessionStorage.getItem(name);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.warn('Failed to read from sessionStorage:', error);
      return null;
    }
  },
  setItem: (name: string, value: any) => {
    try {
      sessionStorage.setItem(name, JSON.stringify(value));
    } catch (error) {
      console.warn('Failed to write to sessionStorage:', error);
    }
  },
  removeItem: (name: string) => {
    try {
      sessionStorage.removeItem(name);
    } catch (error) {
      console.warn('Failed to remove from sessionStorage:', error);
    }
  }
};

// Helper to decode JWT token
const decodeToken = (token: string) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload;
  } catch (error) {
    console.warn('Failed to decode token:', error);
    return null;
  }
};

export const useUnifiedAuthStore = create<UnifiedAuthStore>()(
  devtools(
    (set, get) => {
      // Load initial state from sessionStorage
      const initialState = (() => {
        const stored = sessionStorageAdapter.getItem(SESSION_STORAGE_KEY);
        if (stored && stored.tokens && stored.user) {
          // Verify token is not expired
          const payload = decodeToken(stored.tokens.access_token);
          if (payload && payload.exp > Math.floor(Date.now() / 1000)) {
            return {
              user: stored.user,
              profile: stored.profile || null,
              tokens: stored.tokens,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            };
          }
        }
        return {
          user: null,
          profile: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        };
      })();

      return {
        ...initialState,

        setAuth: (tokens, user, profile) => {
          const newState = {
            tokens,
            user,
            profile: profile || null,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          };
          
          // Persist to sessionStorage
          sessionStorageAdapter.setItem(SESSION_STORAGE_KEY, newState);
          
          set(newState, false, 'setAuth');
          console.log('✅ Auth set in unified store for user:', user.email);
        },

        clearAuth: () => {
          const clearedState = {
            user: null,
            profile: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          };
          
          // Clear sessionStorage
          sessionStorageAdapter.removeItem(SESSION_STORAGE_KEY);
          
          // Clear any legacy localStorage keys
          const legacyKeys = ['access_token', 'auth_tokens', 'refresh_token'];
          legacyKeys.forEach(key => {
            try {
              localStorage.removeItem(key);
            } catch (error) {
              console.warn(`Failed to clear legacy key ${key}:`, error);
            }
          });
          
          set(clearedState, false, 'clearAuth');
          console.log('🗑️ Auth cleared from unified store');
        },

        setLoading: (loading) => set({ isLoading: loading }, false, 'setLoading'),

        setError: (error) => set({ error }, false, 'setError'),

        getAccessToken: () => {
          const { tokens, isAuthenticated } = get();
          return isAuthenticated && tokens ? tokens.access_token : null;
        },

        getRefreshToken: () => {
          const { tokens, isAuthenticated } = get();
          return isAuthenticated && tokens ? tokens.refresh_token : null;
        },

        isTokenExpired: () => {
          const { tokens } = get();
          if (!tokens) return true;
          
          const payload = decodeToken(tokens.access_token);
          if (!payload) return true;
          
          const currentTime = Math.floor(Date.now() / 1000);
          return payload.exp < currentTime;
        },

        getFullName: () => {
          const { user } = get();
          if (!user) return 'Guest';
          return `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email;
        },

        migrateFromLegacy: () => {
          console.log('🔄 Migrating from legacy auth systems...');
          
          // Check for existing auth in various legacy locations
          let migratedTokens: AuthTokens | null = null;
          let migratedUser: User | null = null;
          
          try {
            // Try auth_tokens first (most complete)
            const authTokensStr = localStorage.getItem('auth_tokens');
            if (authTokensStr) {
              const parsed = JSON.parse(authTokensStr);
              if (parsed.access_token && parsed.user) {
                migratedTokens = {
                  access_token: parsed.access_token,
                  refresh_token: parsed.refresh_token || '',
                  token_type: parsed.token_type || 'bearer',
                  expires_in: parsed.expires_in || 900
                };
                migratedUser = parsed.user;
              }
            }
            
            // Fallback to separate access_token
            if (!migratedTokens) {
              const accessToken = localStorage.getItem('access_token');
              if (accessToken) {
                const payload = decodeToken(accessToken);
                if (payload && payload.exp > Math.floor(Date.now() / 1000)) {
                  migratedTokens = {
                    access_token: accessToken,
                    refresh_token: localStorage.getItem('refresh_token') || '',
                    token_type: 'bearer',
                    expires_in: 900
                  };
                  
                  // Try to reconstruct user from token
                  migratedUser = {
                    id: parseInt(payload.sub || '0'),
                    email: payload.email || 'unknown@example.com',
                    first_name: payload.first_name || 'Unknown',
                    last_name: payload.last_name || 'User',
                    is_active: true,
                    status: 'active',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                  } as User;
                }
              }
            }
            
            // Check Zustand persist store
            if (!migratedTokens) {
              const zustandStore = localStorage.getItem('wealthpath-auth-store');
              if (zustandStore) {
                const parsed = JSON.parse(zustandStore);
                if (parsed.state && parsed.state.tokens && parsed.state.user) {
                  migratedTokens = parsed.state.tokens;
                  migratedUser = parsed.state.user;
                }
              }
            }
            
            if (migratedTokens && migratedUser) {
              get().setAuth(migratedTokens, migratedUser);
              console.log('✅ Successfully migrated auth for user:', migratedUser.email);
              
              // Clean up legacy storage
              const legacyKeys = [
                'access_token', 
                'auth_tokens', 
                'refresh_token', 
                'wealthpath-auth-store'
              ];
              legacyKeys.forEach(key => {
                try {
                  localStorage.removeItem(key);
                } catch (error) {
                  console.warn(`Failed to clear legacy key ${key}:`, error);
                }
              });
              
              return true;
            } else {
              console.log('📝 No valid legacy auth found to migrate');
              return false;
            }
            
          } catch (error) {
            console.error('❌ Failed to migrate legacy auth:', error);
            return false;
          }
        },
      };
    },
    {
      name: 'unified-auth-store',
    }
  )
);

// Export a convenience hook for components that only need auth status
export const useAuth = () => {
  const store = useUnifiedAuthStore();
  return {
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    user: store.user,
    getAccessToken: store.getAccessToken,
    logout: store.clearAuth,
  };
};

// Export a convenience hook for API calls
export const useAuthToken = () => {
  const getAccessToken = useUnifiedAuthStore(state => state.getAccessToken);
  return getAccessToken();
};

console.log('🏪 Unified Auth Store initialized');