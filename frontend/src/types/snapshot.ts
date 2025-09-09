export interface SnapshotEntry {
  id: number;
  category: string;
  subcategory?: string;
  name: string;
  institution?: string;
  account_type?: string;
  amount: number;
  interest_rate?: number;
}

export interface SnapshotGoal {
  id: number;
  goal_name: string;
  target_amount: number;
  current_amount: number;
  target_date?: string;
  completion_percentage?: number;
}

export interface Snapshot {
  id: number;
  user_id: number;
  snapshot_date: string;
  snapshot_name?: string;
  net_worth?: number;
  total_assets?: number;
  total_liabilities?: number;
  monthly_income?: number;
  monthly_expenses?: number;
  savings_rate?: number;
  age?: number;
  employment_status?: string;
  notes?: string;
  created_at: string;
  entries: SnapshotEntry[];
  goals: SnapshotGoal[];
}

export interface SnapshotCreate {
  name?: string;
}

export interface TimelineData {
  dates: string[];
  net_worth: number[];
  assets: number[];
  liabilities: number[];
}

export interface LastSnapshotInfo {
  last_snapshot_date?: string;
  days_since_last?: number;
  can_create_new: boolean;
}