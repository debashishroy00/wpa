/**
 * WealthPath AI - Authentication Store (Zustand)
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { User, UserProfile, AuthTokens, AuthState } from '../types/auth';
import { apiClient } from '../utils/api-simple';

interface AuthStore extends AuthState {
  // Actions
  setUser: (user: User | undefined) => void;
  setProfile: (profile: UserProfile | undefined) => void;
  setTokens: (tokens: AuthTokens | undefined) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | undefined) => void;
  
  // Auth actions
  login: (tokens: AuthTokens, user: User, profile?: UserProfile) => void;
  logout: () => void;
  updateProfile: (profile: Partial<UserProfile>) => void;
  
  // Computed
  getFullName: () => string;
  isTokenExpired: () => boolean;
}

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        user: undefined,
        profile: undefined,
        tokens: undefined,
        isAuthenticated: false,
        isLoading: false,
        error: undefined,

        // Setters
        setUser: (user) => 
          set({ user, isAuthenticated: !!user }, false, 'setUser'),

        setProfile: (profile) => 
          set({ profile }, false, 'setProfile'),

        setTokens: (tokens) => {
          if (tokens) {
            apiClient.setTokens(tokens);
          } else {
            apiClient.clearTokens();
          }
          set({ tokens }, false, 'setTokens');
        },

        setLoading: (isLoading) => 
          set({ isLoading }, false, 'setLoading'),

        setError: (error) => 
          set({ error }, false, 'setError'),

        // Auth actions
        login: (tokens, user, profile) => {
          // Store tokens in API client
          apiClient.setTokens(tokens);
          
          set({
            tokens,
            user,
            profile,
            isAuthenticated: true,
            isLoading: false,
            error: undefined,
          }, false, 'login');
        },

        logout: () => {
          // Clear tokens from API client
          apiClient.clearTokens();
          
          set({
            user: undefined,
            profile: undefined,
            tokens: undefined,
            isAuthenticated: false,
            isLoading: false,
            error: undefined,
          }, false, 'logout');
        },

        updateProfile: (profileUpdate) => {
          const currentProfile = get().profile;
          if (currentProfile) {
            const updatedProfile = { ...currentProfile, ...profileUpdate };
            set({ profile: updatedProfile }, false, 'updateProfile');
          }
        },

        // Computed getters
        getFullName: () => {
          const { user } = get();
          if (!user) return '';
          
          const parts = [];
          if (user.first_name) parts.push(user.first_name);
          if (user.last_name) parts.push(user.last_name);
          
          return parts.length > 0 ? parts.join(' ') : user.email;
        },

        isTokenExpired: () => {
          const { tokens } = get();
          if (!tokens) return true;
          
          try {
            // Decode JWT token to check expiration (simplified)
            const payload = JSON.parse(atob(tokens.access_token.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            
            return payload.exp < currentTime;
          } catch (error) {
            console.error('Failed to decode token:', error);
            return true;
          }
        },
      }),
      {
        name: 'wealthpath-auth-store',
        partialize: (state) => ({
          // Persist auth data across sessions
          user: state.user,
          profile: state.profile,
          tokens: state.tokens,
          isAuthenticated: state.isAuthenticated,
        }),
        onRehydrateStorage: () => (state) => {
          console.log('🔄 Auth store rehydrating from localStorage...');
          console.log('📋 Rehydrated state:', state);
          
          // Restore tokens to API client after rehydration
          if (state?.tokens) {
            console.log('✅ Setting tokens in API client from rehydrated state');
            apiClient.setTokens(state.tokens);
          } else {
            console.log('❌ No tokens found in rehydrated state');
          }
        },
      }
    ),
    {
      name: 'auth-store',
    }
  )
);

// Selector hooks for better performance
export const useAuthUser = () => {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const tokens = useAuthStore((state) => state.tokens);
  
  console.log('🔍 useAuthUser called - Auth Store State:', {
    user: user,
    isAuthenticated: isAuthenticated,
    hasTokens: !!tokens,
    tokensDetail: tokens ? {
      access_token: !!tokens.access_token,
      refresh_token: !!tokens.refresh_token
    } : null
  });
  
  // Debug the condition check
  console.log('🔍 Condition check:', {
    userUndefined: !user,
    hasAccessToken: !!tokens?.access_token,
    shouldReconstruct: !user && tokens?.access_token
  });
  
  // If user is undefined but tokens exist (either in store or localStorage), try to reconstruct user from JWT
  let accessToken = tokens?.access_token;
  
  // Fallback: check localStorage if tokens not in store yet (rehydration timing issue)
  if (!accessToken) {
    try {
      // Try both localStorage keys (auth_tokens and the Zustand store key)
      let localStorageTokens = localStorage.getItem('auth_tokens');
      
      if (!localStorageTokens) {
        // Try the Zustand store key
        const zustandStore = localStorage.getItem('wealthpath-auth-store');
        if (zustandStore) {
          const parsedStore = JSON.parse(zustandStore);
          localStorageTokens = JSON.stringify(parsedStore.state?.tokens);
        }
      }
      
      if (localStorageTokens && localStorageTokens !== 'undefined') {
        const parsedTokens = JSON.parse(localStorageTokens);
        accessToken = parsedTokens.access_token;
        console.log('🔄 Found tokens in localStorage but not in store - rehydration timing issue');
      }
    } catch (error) {
      console.error('❌ Failed to parse tokens from localStorage:', error);
    }
  }
  
  if (!user && accessToken) {
    try {
      console.log('🔄 User undefined but tokens exist, reconstructing from JWT...');
      const tokenParts = accessToken.split('.');
      const payload = JSON.parse(atob(tokenParts[1]));
      
      const reconstructedUser = {
        id: parseInt(payload.sub, 10),
        email: payload.email || `user_${payload.sub}@example.com`,
        first_name: payload.first_name || '',
        last_name: payload.last_name || '',
        is_active: true,
        status: 'active' as const,
        created_at: new Date().toISOString()
      };
      
      console.log('✅ Reconstructed user from JWT:', reconstructedUser);
      
      // Update the store with the reconstructed user
      useAuthStore.getState().setUser(reconstructedUser);
      
      return reconstructedUser;
    } catch (error) {
      console.error('❌ Failed to reconstruct user from JWT:', error);
      return user;
    }
  }
  
  return user;
};

export const useUserProfile = () => useAuthStore((state) => state.profile);
export const useAuthTokens = () => useAuthStore((state) => state.tokens);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);