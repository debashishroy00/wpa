import { apiClient } from '../utils/api-simple';
import { Snapshot, SnapshotCreate, TimelineData, LastSnapshotInfo, DetailedSnapshot } from '../types/snapshot';

export const snapshotApi = {
  async createSnapshot(data: SnapshotCreate): Promise<Snapshot> {
    return apiClient.post<Snapshot>('/api/v1/snapshots/', data);
  },

  async getSnapshots(limit = 20, period?: string): Promise<Snapshot[]> {
    const params: any = { limit };
    if (period) {
      params.period = period;
    }
    return apiClient.get<Snapshot[]>('/api/v1/snapshots/', { params });
  },

  async getTimelineData(period?: string): Promise<TimelineData> {
    const params: any = {};
    if (period) {
      params.period = period;
    }
    return apiClient.get<TimelineData>('/api/v1/snapshots/timeline', { params });
  },

  async deleteSnapshot(snapshotId: number): Promise<void> {
    return apiClient.delete<void>(`/api/v1/snapshots/${snapshotId}`);
  },

  async getLastSnapshotInfo(): Promise<LastSnapshotInfo> {
    return apiClient.get<LastSnapshotInfo>('/api/v1/snapshots/last-date');
  },

  async getDetailedSnapshots(limit = 4, period?: string): Promise<DetailedSnapshot[]> {
    const params: any = { limit };
    if (period && period !== 'all') {
      params.period = period;
    }
    return apiClient.get<DetailedSnapshot[]>('/api/v1/snapshots/detailed', { params });
  }
};