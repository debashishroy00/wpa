/**
 * WealthPath AI - Financial Data React Query Hooks
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { financialApi } from '../utils/financial-api';
import { useFinancialStore } from '../stores/financial-store';
import {
  FinancialEntryCreate,
  FinancialEntryUpdate,
  FinancialEntryFilters,
  NetWorthHistoryQuery,
  ApiError,
} from '../types';

// Query Keys
export const financialQueryKeys = {
  all: ['financial'] as const,
  summary: () => [...financialQueryKeys.all, 'summary'] as const,
  entries: (filters?: FinancialEntryFilters) => 
    [...financialQueryKeys.all, 'entries', filters] as const,
  categorizedEntries: () => [...financialQueryKeys.all, 'entries', 'categorized'] as const,
  accounts: () => [...financialQueryKeys.all, 'accounts'] as const,
  dataQuality: () => [...financialQueryKeys.all, 'data-quality'] as const,
  netWorthHistory: (query?: NetWorthHistoryQuery) =>
    [...financialQueryKeys.all, 'net-worth-history', query] as const,
  portfolioAllocation: () => [...financialQueryKeys.all, 'portfolio-allocation'] as const,
};

// Financial Summary Query
export const useFinancialSummaryQuery = () => {
  const { setSummary, setLoading, setError } = useFinancialStore();

  return useQuery({
    queryKey: financialQueryKeys.summary(),
    queryFn: financialApi.getFinancialSummary,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Financial Entries Query
export const useFinancialEntriesQuery = (filters?: FinancialEntryFilters) => {
  const { setEntries, setLoading, setError } = useFinancialStore();

  return useQuery({
    queryKey: financialQueryKeys.entries(filters),
    queryFn: () => financialApi.getFinancialEntries(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Categorized Entries Query (New - fixes NaN issue)
export const useCategorizedEntriesQuery = () => {
  return useQuery({
    queryKey: financialQueryKeys.categorizedEntries(),
    queryFn: () => financialApi.getCategorizedEntries(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

// Financial Accounts Query
export const useFinancialAccountsQuery = () => {
  const { setAccounts, setLoading, setError } = useFinancialStore();

  return useQuery({
    queryKey: financialQueryKeys.accounts(),
    queryFn: financialApi.getFinancialAccounts,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Data Quality Breakdown Query
export const useDataQualityQuery = () => {
  const { setDataQualityBreakdown, setLoading, setError } = useFinancialStore();

  return useQuery({
    queryKey: financialQueryKeys.dataQuality(),
    queryFn: financialApi.getDataQualityBreakdown,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Net Worth History Query
export const useNetWorthHistoryQuery = (query?: NetWorthHistoryQuery) => {
  const { setNetWorthHistory, setLoading, setError } = useFinancialStore();

  return useQuery({
    queryKey: financialQueryKeys.netWorthHistory(query),
    queryFn: () => financialApi.getNetWorthHistory(query),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Mutations
export const useCreateFinancialEntryMutation = () => {
  const queryClient = useQueryClient();
  const { addEntry, setLoading, setError, filters } = useFinancialStore();

  return useMutation({
    mutationFn: (data: FinancialEntryCreate) => financialApi.createFinancialEntry(data),
    onSuccess: (newEntry) => {
      addEntry(newEntry);
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.entries(filters) });
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.summary() });
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.dataQuality() });
    },
  });
};

export const useUpdateFinancialEntryMutation = () => {
  const queryClient = useQueryClient();
  const { updateEntry, setLoading, setError, filters } = useFinancialStore();

  return useMutation({
    mutationFn: ({ id, update }: { id: number; update: FinancialEntryUpdate }) =>
      financialApi.updateFinancialEntry(id, update),
    onSuccess: (updatedEntry) => {
      updateEntry(updatedEntry.id, updatedEntry);
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.entries(filters) });
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.summary() });
    },
  });
};

export const useDeleteFinancialEntryMutation = () => {
  const queryClient = useQueryClient();
  const { removeEntry, setLoading, setError, filters } = useFinancialStore();

  return useMutation({
    mutationFn: (id: number) => financialApi.deleteFinancialEntry(id),
    onSuccess: (_, deletedId) => {
      removeEntry(deletedId.toString());
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.entries(filters) });
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.summary() });
    },
  });
};

export const useCreateNetWorthSnapshotMutation = () => {
  const queryClient = useQueryClient();
  const { setLoading, setError } = useFinancialStore();

  return useMutation({
    mutationFn: financialApi.createNetWorthSnapshot,
    onSuccess: () => {
      // Invalidate net worth history to include new snapshot
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.netWorthHistory() });
      queryClient.invalidateQueries({ queryKey: financialQueryKeys.summary() });
    },
  });
};

export const useTriggerDataSyncMutation = () => {
  const queryClient = useQueryClient();
  const { setLoading, setError } = useFinancialStore();

  return useMutation({
    mutationFn: financialApi.triggerDataSync,
    onSuccess: () => {
      // Invalidate all data queries as sync may update everything
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: financialQueryKeys.all });
      }, 2000); // Wait 2 seconds for sync to potentially complete
    },
  });
};

// Portfolio Allocation Query
export const usePortfolioAllocationQuery = () => {
  return useQuery({
    queryKey: financialQueryKeys.portfolioAllocation(),
    queryFn: () => financialApi.getPortfolioAllocation(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};