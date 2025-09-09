import axios from 'axios';
import { Snapshot, SnapshotCreate, TimelineData, LastSnapshotInfo } from '../types/snapshot';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const snapshotApi = {
  async createSnapshot(data: SnapshotCreate): Promise<Snapshot> {
    const response = await axios.post(`${API_BASE}/api/v1/snapshots/`, data);
    return response.data;
  },

  async getSnapshots(limit = 20): Promise<Snapshot[]> {
    const response = await axios.get(`${API_BASE}/api/v1/snapshots/`, { params: { limit } });
    return response.data;
  },

  async getTimelineData(): Promise<TimelineData> {
    const response = await axios.get(`${API_BASE}/api/v1/snapshots/timeline`);
    return response.data;
  },

  async deleteSnapshot(snapshotId: number): Promise<void> {
    await axios.delete(`${API_BASE}/api/v1/snapshots/${snapshotId}`);
  },

  async getLastSnapshotInfo(): Promise<LastSnapshotInfo> {
    const response = await axios.get(`${API_BASE}/api/v1/snapshots/last-date`);
    return response.data;
  }
};