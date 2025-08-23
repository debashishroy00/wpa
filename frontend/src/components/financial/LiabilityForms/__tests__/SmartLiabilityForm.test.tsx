import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SmartLiabilityForm from '../SmartLiabilityForm';
import { EntryCategory, FrequencyType } from '../../../../types/financial';

// Mock the mutation hooks
vi.mock('../../../../hooks/use-financial-queries', () => ({
  useCreateFinancialEntryMutation: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ id: '1', success: true }),
    isPending: false,
  }),
  useUpdateFinancialEntryMutation: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ id: '1', success: true }),
    isPending: false,
  }),
}));

describe('SmartLiabilityForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    subcategory: 'mortgage_real_estate',
    onSubmit: mockOnSubmit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Form Rendering', () => {
    it('should render mortgage form for mortgage_real_estate subcategory', () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/current balance/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/interest rate/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/original term/i)).toBeInTheDocument();
    });

    it('should render credit card form for credit_cards subcategory', () => {
      render(<SmartLiabilityForm {...defaultProps} subcategory="credit_cards" />);
      
      expect(screen.getByLabelText(/card name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/current balance/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/credit limit/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/apr/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);
      
      // Form should not submit without required fields
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should validate interest rate range', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      const interestRateInput = screen.getByLabelText(/interest rate/i);
      await userEvent.type(interestRateInput, '100'); // Invalid - too high
      
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);
      
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should handle boolean fields correctly', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      // Fill in required fields
      await userEvent.type(screen.getByLabelText(/description/i), 'Test Mortgage');
      await userEvent.type(screen.getByLabelText(/current balance/i), '300000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '2.75');
      await userEvent.type(screen.getByLabelText(/original term/i), '30');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '25');
      
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            description: 'Test Mortgage',
            amount: 300000,
            interest_rate: 2.75,
            loan_term_months: 360, // 30 years * 12
            remaining_months: 300, // 25 years * 12
            is_fixed_rate: true, // Should be boolean, not string
          })
        );
      });
    });
  });

  describe('Data Submission', () => {
    it('should submit correct data structure for mortgage', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      // Fill in the form
      await userEvent.type(screen.getByLabelText(/description/i), 'Home Mortgage');
      await userEvent.type(screen.getByLabelText(/current balance/i), '313026');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '2.75');
      await userEvent.type(screen.getByLabelText(/original term/i), '20');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '14');
      await userEvent.type(screen.getByLabelText(/monthly payment/i), '2264');
      await userEvent.type(screen.getByLabelText(/property value/i), '1050000');
      
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            category: EntryCategory.LIABILITIES,
            subcategory: 'mortgage_real_estate',
            description: 'Home Mortgage',
            amount: 313026,
            currency: 'USD',
            frequency: FrequencyType.ONE_TIME,
            interest_rate: 2.75,
            loan_term_months: 240, // 20 * 12
            remaining_months: 168, // 14 * 12
            minimum_payment: 2264,
            is_fixed_rate: true,
            original_amount: 313026,
            loan_details: expect.any(String), // JSON string
          })
        );
      });
    });

    it('should handle loan_details as JSON string', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      await userEvent.type(screen.getByLabelText(/description/i), 'Test');
      await userEvent.type(screen.getByLabelText(/current balance/i), '100000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '3.5');
      await userEvent.type(screen.getByLabelText(/original term/i), '30');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '20');
      
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        const callArgs = mockOnSubmit.mock.calls[0][0];
        expect(typeof callArgs.loan_details).toBe('string');
        
        // Should be valid JSON
        const parsed = JSON.parse(callArgs.loan_details);
        expect(parsed).toHaveProperty('current_balance');
        expect(parsed).toHaveProperty('interest_rate');
      });
    });
  });

  describe('Edit Mode', () => {
    const existingEntry = {
      id: '7',
      description: 'Existing Mortgage',
      amount: 250000,
      interest_rate: 3.25,
      loan_term_months: 360,
      remaining_months: 240,
      minimum_payment: 1800,
      is_fixed_rate: true,
      loan_details: '{"property_value": 800000}',
    };

    it('should populate form with existing data in edit mode', () => {
      render(
        <SmartLiabilityForm
          {...defaultProps}
          entry={existingEntry}
          isEditing={true}
        />
      );
      
      expect(screen.getByDisplayValue('Existing Mortgage')).toBeInTheDocument();
      expect(screen.getByDisplayValue('250000')).toBeInTheDocument();
      expect(screen.getByDisplayValue('3.25')).toBeInTheDocument();
      expect(screen.getByDisplayValue('30')).toBeInTheDocument(); // 360 months / 12
      expect(screen.getByDisplayValue('20')).toBeInTheDocument(); // 240 months / 12
    });

    it('should show Update button in edit mode', () => {
      render(
        <SmartLiabilityForm
          {...defaultProps}
          entry={existingEntry}
          isEditing={true}
        />
      );
      
      expect(screen.getByRole('button', { name: /update liability/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /add liability/i })).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display validation errors', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      // Submit empty form
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);
      
      // Should not call onSubmit
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should handle API submission errors', async () => {
      const mockErrorSubmit = vi.fn().mockRejectedValue(
        new Error('Network error')
      );
      
      render(
        <SmartLiabilityForm
          {...defaultProps}
          onSubmit={mockErrorSubmit}
        />
      );
      
      // Fill valid data
      await userEvent.type(screen.getByLabelText(/description/i), 'Test');
      await userEvent.type(screen.getByLabelText(/current balance/i), '100000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '3.5');
      await userEvent.type(screen.getByLabelText(/original term/i), '30');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '20');
      
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      
      // Mock window.alert
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          expect.stringContaining('Failed to submit form')
        );
      });
      
      alertSpy.mockRestore();
    });
  });

  describe('Form Insights', () => {
    it('should display insights for low interest rate', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      await userEvent.type(screen.getByLabelText(/current balance/i), '300000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '2.5');
      await userEvent.type(screen.getByLabelText(/monthly payment/i), '2000');
      
      await waitFor(() => {
        expect(screen.getByText(/excellent rate/i)).toBeInTheDocument();
      });
    });

    it('should display insights for high interest rate', async () => {
      render(<SmartLiabilityForm {...defaultProps} />);
      
      await userEvent.type(screen.getByLabelText(/current balance/i), '10000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '18');
      
      await waitFor(() => {
        expect(screen.getByText(/high rate.*prioritize/i)).toBeInTheDocument();
      });
    });
  });
});