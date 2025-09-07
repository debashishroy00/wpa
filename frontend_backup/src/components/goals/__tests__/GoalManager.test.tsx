/**
 * WealthPath AI - GoalManager Component Tests
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { jest } from '@jest/globals';
import GoalManager from '../GoalManager';
import { goalsApi } from '../../../utils/goal-api';

// Mock the goals API
jest.mock('../../../utils/goal-api');
const mockedGoalsApi = goalsApi as jest.Mocked<typeof goalsApi>;

// Mock data
const mockGoals = [
  {
    goal_id: '123e4567-e89b-12d3-a456-426614174000',
    user_id: 1,
    category: 'retirement',
    name: 'Retirement Fund',
    description: 'Long-term retirement savings',
    target_amount: 1000000.00,
    target_date: '2045-12-31',
    priority: 1,
    status: 'active',
    params: {
      retirement_age: 65,
      annual_spending: 50000,
      current_age: 30
    },
    progress_percentage: 15.50,
    current_amount: 155000.00,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    goal_id: '123e4567-e89b-12d3-a456-426614174001',
    user_id: 1,
    category: 'education',
    name: 'College Fund',
    description: 'Savings for child education',
    target_amount: 200000.00,
    target_date: '2035-08-31',
    priority: 2,
    status: 'active',
    params: {
      degree_type: 'undergraduate',
      institution_type: 'public',
      start_year: 2035
    },
    progress_percentage: 8.25,
    current_amount: 16500.00,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

const mockSummary = {
  active_goals: 2,
  achieved_goals: 0,
  total_target: 1200000.00,
  nearest_deadline: '2035-08-31',
  average_progress: 11.875
};

const mockConflicts = [];

const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
};

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('GoalManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mock responses
    mockedGoalsApi.getGoals.mockResolvedValue(mockGoals);
    mockedGoalsApi.getGoalSummary.mockResolvedValue(mockSummary);
    mockedGoalsApi.getGoalConflicts.mockResolvedValue(mockConflicts);
    mockedGoalsApi.getCategories.mockResolvedValue({
      retirement: {
        name: 'Retirement',
        description: 'Long-term retirement savings',
        required_params: ['retirement_age', 'annual_spending', 'current_age'],
        typical_timeline: '20-40 years'
      },
      education: {
        name: 'Education',
        description: 'College, graduate school, or professional education',
        required_params: ['degree_type', 'institution_type', 'start_year'],
        typical_timeline: '1-10 years'
      }
    });
  });

  it('renders goal manager with summary cards', async () => {
    renderWithQueryClient(<GoalManager />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Active Goals')).toBeInTheDocument();
    });

    // Check summary cards
    expect(screen.getByText('2')).toBeInTheDocument(); // active goals count
    expect(screen.getByText('$1,200,000')).toBeInTheDocument(); // total target
    expect(screen.getByText('11.9%')).toBeInTheDocument(); // average progress
  });

  it('displays list of goals', async () => {
    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
      expect(screen.getByText('College Fund')).toBeInTheDocument();
    });

    // Check goal details
    expect(screen.getByText('$1,000,000')).toBeInTheDocument();
    expect(screen.getByText('$200,000')).toBeInTheDocument();
    expect(screen.getByText('15.5%')).toBeInTheDocument();
    expect(screen.getByText('8.3%')).toBeInTheDocument();
  });

  it('opens create goal modal when add button is clicked', async () => {
    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('Add New Goal')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add New Goal');
    fireEvent.click(addButton);

    // Check if modal opens (assuming it shows a form or modal title)
    await waitFor(() => {
      expect(screen.getByText('Create New Goal')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    // Mock loading state
    mockedGoalsApi.getGoals.mockImplementation(() => new Promise(() => {}));
    mockedGoalsApi.getGoalSummary.mockImplementation(() => new Promise(() => {}));

    renderWithQueryClient(<GoalManager />);

    // Should show loading indicators
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock error
    const errorMessage = 'Failed to fetch goals';
    mockedGoalsApi.getGoals.mockRejectedValue(new Error(errorMessage));
    mockedGoalsApi.getGoalSummary.mockRejectedValue(new Error(errorMessage));

    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('filters goals by status', async () => {
    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
    });

    // Find and click status filter
    const statusFilter = screen.getByDisplayValue('All');
    fireEvent.change(statusFilter, { target: { value: 'active' } });

    // Verify the API was called with correct filter
    expect(mockedGoalsApi.getGoals).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'active' })
    );
  });

  it('filters goals by category', async () => {
    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
    });

    // Find and click category filter
    const categoryFilter = screen.getByDisplayValue('All Categories');
    fireEvent.change(categoryFilter, { target: { value: 'retirement' } });

    // Verify the API was called with correct filter
    expect(mockedGoalsApi.getGoals).toHaveBeenCalledWith(
      expect.objectContaining({ category: 'retirement' })
    );
  });

  it('displays empty state when no goals exist', async () => {
    mockedGoalsApi.getGoals.mockResolvedValue([]);
    mockedGoalsApi.getGoalSummary.mockResolvedValue({
      active_goals: 0,
      achieved_goals: 0,
      total_target: 0,
      nearest_deadline: null,
      average_progress: 0
    });

    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('No goals found')).toBeInTheDocument();
    });

    expect(screen.getByText('Create your first financial goal to get started')).toBeInTheDocument();
  });

  it('refreshes data when refresh button is clicked', async () => {
    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
    });

    const refreshButton = screen.getByLabelText('Refresh');
    fireEvent.click(refreshButton);

    // Verify APIs are called again
    expect(mockedGoalsApi.getGoals).toHaveBeenCalledTimes(2);
    expect(mockedGoalsApi.getGoalSummary).toHaveBeenCalledTimes(2);
  });

  it('opens goal details when goal card is clicked', async () => {
    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
    });

    const goalCard = screen.getByText('Retirement Fund').closest('.goal-card');
    fireEvent.click(goalCard!);

    // Should open goal details modal or navigate to details
    await waitFor(() => {
      expect(screen.getByText('Goal Details')).toBeInTheDocument();
    });
  });

  it('shows conflicts warning when conflicts exist', async () => {
    const mockConflictsWithData = [
      {
        goal1_id: '123e4567-e89b-12d3-a456-426614174000',
        goal1_name: 'Retirement Fund',
        goal2_id: '123e4567-e89b-12d3-a456-426614174001',
        goal2_name: 'College Fund',
        conflict_type: 'timeline_overlap',
        severity: 'medium'
      }
    ];

    mockedGoalsApi.getGoalConflicts.mockResolvedValue(mockConflictsWithData);

    renderWithQueryClient(<GoalManager />);

    await waitFor(() => {
      expect(screen.getByText(/conflict/i)).toBeInTheDocument();
    });

    // Should show warning indicator
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });
});