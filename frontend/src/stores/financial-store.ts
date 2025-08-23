/**
 * WealthPath AI - Financial Data Store (Zustand)
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  FinancialEntry,
  FinancialEntryCreate,
  FinancialEntryUpdate,
  FinancialEntryFilters,
  FinancialSummary,
  FinancialAccount,
  NetWorthSnapshot,
  DataQualityBreakdown,
  FinancialUIState,
  LoadingState,
  ErrorState,
} from '../types';

interface FinancialStore extends FinancialUIState {
  // Data state
  summary?: FinancialSummary;
  entries: FinancialEntry[];
  accounts: FinancialAccount[];
  netWorthHistory: NetWorthSnapshot[];
  dataQualityBreakdown?: DataQualityBreakdown;

  // Loading states
  loading: LoadingState;
  errors: ErrorState;

  // UI actions
  setSelectedEntry: (entry?: FinancialEntry) => void;
  setCreateModalOpen: (open: boolean) => void;
  setEditModalOpen: (open: boolean) => void;
  setFilters: (filters: Partial<FinancialEntryFilters>) => void;
  clearError: (key: string) => void;
  clearAllErrors: () => void;

  // Data actions
  setSummary: (summary: FinancialSummary) => void;
  setEntries: (entries: FinancialEntry[]) => void;
  addEntry: (entry: FinancialEntry) => void;
  updateEntry: (id: string, update: Partial<FinancialEntry>) => void;
  removeEntry: (id: string) => void;
  setAccounts: (accounts: FinancialAccount[]) => void;
  setNetWorthHistory: (history: NetWorthSnapshot[]) => void;
  setDataQualityBreakdown: (breakdown: DataQualityBreakdown) => void;

  // Loading actions
  setLoading: (key: string, loading: boolean) => void;
  setError: (key: string, error: string | null) => void;

  // Computed getters
  getTotalAssets: () => number;
  getTotalLiabilities: () => number;
  getNetWorth: () => number;
  getEntriesByCategory: (category: string) => FinancialEntry[];
  getLatestNetWorthSnapshot: () => NetWorthSnapshot | undefined;
  getEntriesCount: () => number;
  getConnectedAccountsCount: () => number;
}

export const useFinancialStore = create<FinancialStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        summary: undefined,
        entries: [],
        accounts: [],
        netWorthHistory: [],
        dataQualityBreakdown: undefined,

        // UI state
        isLoading: false,
        error: undefined,
        selectedEntry: undefined,
        isCreateModalOpen: false,
        isEditModalOpen: false,
        filters: {},

        // Loading and error states
        loading: {},
        errors: {},

        // UI actions
        setSelectedEntry: (entry) => set({ selectedEntry: entry }, false, 'setSelectedEntry'),

        setCreateModalOpen: (open) => set({ isCreateModalOpen: open }, false, 'setCreateModalOpen'),

        setEditModalOpen: (open) => set({ isEditModalOpen: open }, false, 'setEditModalOpen'),

        setFilters: (newFilters) =>
          set(
            (state) => ({
              filters: { ...state.filters, ...newFilters },
            }),
            false,
            'setFilters'
          ),

        clearError: (key) =>
          set(
            (state) => ({
              errors: { ...state.errors, [key]: null },
            }),
            false,
            'clearError'
          ),

        clearAllErrors: () => set({ errors: {} }, false, 'clearAllErrors'),

        // Data actions
        setSummary: (summary) => set({ summary }, false, 'setSummary'),

        setEntries: (entries) => set({ entries }, false, 'setEntries'),

        addEntry: (entry) =>
          set(
            (state) => ({
              entries: [entry, ...state.entries],
            }),
            false,
            'addEntry'
          ),

        updateEntry: (id, update) =>
          set(
            (state) => ({
              entries: state.entries.map((entry) =>
                entry.id === id ? { ...entry, ...update } : entry
              ),
            }),
            false,
            'updateEntry'
          ),

        removeEntry: (id) =>
          set(
            (state) => ({
              entries: state.entries.filter((entry) => entry.id !== id),
            }),
            false,
            'removeEntry'
          ),

        setAccounts: (accounts) => set({ accounts }, false, 'setAccounts'),

        setNetWorthHistory: (netWorthHistory) =>
          set({ netWorthHistory }, false, 'setNetWorthHistory'),

        setDataQualityBreakdown: (dataQualityBreakdown) =>
          set({ dataQualityBreakdown }, false, 'setDataQualityBreakdown'),

        // Loading actions
        setLoading: (key, loading) =>
          set(
            (state) => ({
              loading: { ...state.loading, [key]: loading },
              isLoading: loading, // Update global loading state
            }),
            false,
            'setLoading'
          ),

        setError: (key, error) =>
          set(
            (state) => ({
              errors: { ...state.errors, [key]: error },
              error: error || undefined, // Update global error state
            }),
            false,
            'setError'
          ),

        // Computed getters
        getTotalAssets: () => {
          const { summary } = get();
          return summary?.total_assets || 0;
        },

        getTotalLiabilities: () => {
          const { summary } = get();
          return summary?.total_liabilities || 0;
        },

        getNetWorth: () => {
          const { summary } = get();
          return summary?.net_worth || 0;
        },

        getEntriesByCategory: (category) => {
          const { entries } = get();
          return entries.filter((entry) => entry.category === category);
        },

        getLatestNetWorthSnapshot: () => {
          const { netWorthHistory } = get();
          return netWorthHistory.length > 0 ? netWorthHistory[0] : undefined;
        },

        getEntriesCount: () => {
          const { entries } = get();
          return entries.length;
        },

        getConnectedAccountsCount: () => {
          const { accounts } = get();
          return accounts.filter((account) => account.is_active && !account.is_manual).length;
        },
      }),
      {
        name: 'wealthpath-financial-store',
        partialize: (state) => ({
          // Only persist certain parts of the state
          summary: state.summary,
          entries: state.entries,
          accounts: state.accounts,
          filters: state.filters,
        }),
      }
    ),
    {
      name: 'financial-store',
    }
  )
);

// Selector hooks for better performance
export const useFinancialSummary = () => useFinancialStore((state) => state.summary);
export const useFinancialEntries = () => useFinancialStore((state) => state.entries);
export const useFinancialAccounts = () => useFinancialStore((state) => state.accounts);
export const useNetWorthHistory = () => useFinancialStore((state) => state.netWorthHistory);
export const useDataQualityBreakdown = () => useFinancialStore((state) => state.dataQualityBreakdown);
export const useFinancialLoading = () => useFinancialStore((state) => state.loading);
export const useFinancialErrors = () => useFinancialStore((state) => state.errors);

// UI state selectors
export const useSelectedFinancialEntry = () => useFinancialStore((state) => state.selectedEntry);
export const useFinancialModals = () =>
  useFinancialStore((state) => ({
    isCreateModalOpen: state.isCreateModalOpen,
    isEditModalOpen: state.isEditModalOpen,
  }));
export const useFinancialFilters = () => useFinancialStore((state) => state.filters);