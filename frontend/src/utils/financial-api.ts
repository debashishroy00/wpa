/**
 * WealthPath AI - Financial API Service
 */
import { apiClient } from './api';
import {
  FinancialEntry,
  FinancialEntryCreate,
  FinancialEntryUpdate,
  FinancialEntryFilters,
  FinancialSummary,
  FinancialAccount,
  NetWorthSnapshot,
  NetWorthHistoryQuery,
  DataQualityBreakdown,
  DataSync,
} from '../types/financial';

export class FinancialApiService {
  private readonly baseUrl = '/api/v1/financial';

  // Financial Summary
  async getFinancialSummary(): Promise<FinancialSummary> {
    return apiClient.get(`${this.baseUrl}/summary`);
  }

  // Financial Entries CRUD
  async getFinancialEntries(filters?: FinancialEntryFilters): Promise<FinancialEntry[]> {
    const params = new URLSearchParams();
    
    if (filters?.category) params.append('category', filters.category);
    if (filters?.data_quality) params.append('data_quality', filters.data_quality);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`${this.baseUrl}/entries${queryString}`);
  }

  // Categorized Entries (New - fixes NaN issue)
  async getCategorizedEntries(): Promise<any> {
    const data = await apiClient.get(`${this.baseUrl}/entries/categorized`);
    
    console.log('Categorized entries data received:', data); // Debug log
    return data;
  }

  async createFinancialEntry(entry: FinancialEntryCreate): Promise<FinancialEntry> {
    return apiClient.post(`${this.baseUrl}/entries`, entry);
  }

  async updateFinancialEntry(id: number, update: FinancialEntryUpdate): Promise<FinancialEntry> {
    return apiClient.put(`${this.baseUrl}/entries/${id}`, update);
  }

  async deleteFinancialEntry(id: number): Promise<{ message: string }> {
    return apiClient.delete(`${this.baseUrl}/entries/${id}`);
  }

  // Financial Accounts
  async getFinancialAccounts(): Promise<FinancialAccount[]> {
    return apiClient.get(`${this.baseUrl}/accounts`);
  }

  // Data Quality Analytics
  async getDataQualityBreakdown(): Promise<DataQualityBreakdown> {
    return apiClient.get(`${this.baseUrl}/data-quality`);
  }

  // Net Worth Tracking
  async getNetWorthHistory(query?: NetWorthHistoryQuery): Promise<NetWorthSnapshot[]> {
    const params = new URLSearchParams();
    if (query?.days) params.append('days', query.days.toString());
    
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`${this.baseUrl}/net-worth/history${queryString}`);
  }

  async createNetWorthSnapshot(): Promise<{
    message: string;
    snapshot_id: number;
    net_worth: number;
    data_quality_score: string;
  }> {
    return apiClient.post(`${this.baseUrl}/net-worth/snapshot`);
  }

  // Portfolio Allocation
  async getPortfolioAllocation(): Promise<any> {
    return apiClient.get(`${this.baseUrl}/portfolio-allocation`);
  }

  // Data Synchronization
  async triggerDataSync(): Promise<DataSync> {
    return apiClient.post(`${this.baseUrl}/sync`);
  }
}

// Create singleton instance
export const financialApi = new FinancialApiService();