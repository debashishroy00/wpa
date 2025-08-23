import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import FinancialEntryForm from '../FinancialEntryForm';
import { EntryCategory, FrequencyType } from '../../../types/financial';
import { apiClient } from '../../../utils/api';

// Mock API client
vi.mock('../../../utils/api', () => ({
  apiClient: {
    post: vi.fn(),
    put: vi.fn(),
    get: vi.fn(),
  },
}));

describe('Liability Form Integration Tests', () => {
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  describe('Create Liability Flow', () => {
    it('should successfully create a mortgage with enhanced fields', async () => {
      const mockResponse = {
        id: '67',
        category: 'liabilities',
        description: 'Home Mortgage',
        amount: 313026,
        interest_rate: 2.75,
        loan_term_months: 240,
        minimum_payment: 2234,
        is_fixed_rate: true,
        loan_details: '{"property_value": 1200000}',
      };

      (apiClient.post as any).mockResolvedValue(mockResponse);

      const mockOnSuccess = vi.fn();
      
      render(
        <FinancialEntryForm onSuccess={mockOnSuccess} />,
        { wrapper }
      );

      // Select liability category
      const categorySelect = screen.getByLabelText(/category/i);
      await userEvent.selectOptions(categorySelect, EntryCategory.LIABILITIES);

      // Select mortgage subcategory
      const subcategorySelect = screen.getByLabelText(/subcategory/i);
      await userEvent.selectOptions(subcategorySelect, 'mortgage_real_estate');

      // SmartLiabilityForm should now be rendered
      await waitFor(() => {
        expect(screen.getByText(/smart form active/i)).toBeInTheDocument();
      });

      // Fill in mortgage details
      await userEvent.type(screen.getByLabelText(/description/i), 'Home Mortgage');
      await userEvent.type(screen.getByLabelText(/current balance/i), '313026');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '2.75');
      await userEvent.type(screen.getByLabelText(/original term/i), '20');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '14');
      await userEvent.type(screen.getByLabelText(/monthly payment/i), '2234');
      await userEvent.type(screen.getByLabelText(/property value/i), '1200000');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /add liability/i });
      await userEvent.click(submitButton);

      // Verify API was called with correct data
      await waitFor(() => {
        expect(apiClient.post).toHaveBeenCalledWith(
          '/api/v1/financial/entries',
          expect.objectContaining({
            category: EntryCategory.LIABILITIES,
            subcategory: 'mortgage_real_estate',
            description: 'Home Mortgage',
            amount: 313026,
            interest_rate: 2.75,
            loan_term_months: 240,
            minimum_payment: 2234,
            is_fixed_rate: true,
            loan_details: expect.any(String),
          })
        );
      });

      // Verify success callback was called
      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it('should handle 422 validation errors correctly', async () => {
      const validationError = {
        response: {
          status: 422,
          data: {
            detail: [
              {
                loc: ['body', 'update', 'loan_details'],
                msg: 'Invalid JSON format',
                type: 'value_error',
              },
            ],
          },
        },
      };

      (apiClient.post as any).mockRejectedValue(validationError);

      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

      render(<FinancialEntryForm />, { wrapper });

      // Select liability and mortgage
      await userEvent.selectOptions(screen.getByLabelText(/category/i), EntryCategory.LIABILITIES);
      await userEvent.selectOptions(screen.getByLabelText(/subcategory/i), 'mortgage_real_estate');

      // Fill minimal required fields
      await userEvent.type(screen.getByLabelText(/description/i), 'Test');
      await userEvent.type(screen.getByLabelText(/current balance/i), '100000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '3.5');
      await userEvent.type(screen.getByLabelText(/original term/i), '30');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '20');

      // Submit
      await userEvent.click(screen.getByRole('button', { name: /add liability/i }));

      // Should show error alert with details
      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          expect.stringContaining('body.update.loan_details: Invalid JSON format')
        );
      });

      alertSpy.mockRestore();
    });
  });

  describe('Update Liability Flow', () => {
    const existingEntry = {
      id: '7',
      category: EntryCategory.LIABILITIES,
      subcategory: 'mortgage_real_estate',
      description: 'Existing Mortgage',
      amount: 250000,
      interest_rate: 3.25,
      loan_term_months: 360,
      remaining_months: 240,
      minimum_payment: 1800,
      is_fixed_rate: true,
      loan_details: '{"property_value": 800000}',
    };

    it('should successfully update a mortgage with enhanced fields', async () => {
      const mockResponse = {
        ...existingEntry,
        interest_rate: 2.75,
        amount: 313026,
      };

      (apiClient.put as any).mockResolvedValue(mockResponse);

      const mockOnSuccess = vi.fn();
      
      render(
        <FinancialEntryForm
          entry={existingEntry as any}
          onSuccess={mockOnSuccess}
        />,
        { wrapper }
      );

      // Should show SmartLiabilityForm for mortgage
      await waitFor(() => {
        expect(screen.getByText(/smart form active/i)).toBeInTheDocument();
      });

      // Form should be pre-populated
      expect(screen.getByDisplayValue('Existing Mortgage')).toBeInTheDocument();

      // Update interest rate
      const interestRateInput = screen.getByLabelText(/interest rate/i);
      await userEvent.clear(interestRateInput);
      await userEvent.type(interestRateInput, '2.75');

      // Update amount
      const amountInput = screen.getByLabelText(/current balance/i);
      await userEvent.clear(amountInput);
      await userEvent.type(amountInput, '313026');

      // Submit update
      const updateButton = screen.getByRole('button', { name: /update liability/i });
      await userEvent.click(updateButton);

      // Verify API was called with correct update data
      await waitFor(() => {
        expect(apiClient.put).toHaveBeenCalledWith(
          '/api/v1/financial/entries/7',
          expect.objectContaining({
            description: 'Existing Mortgage',
            amount: 313026,
            interest_rate: 2.75,
            loan_term_months: 360,
            remaining_months: 240,
            minimum_payment: 1800,
            is_fixed_rate: true,
          })
        );
      });

      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it('should filter out undefined values in update payload', async () => {
      (apiClient.put as any).mockResolvedValue({ success: true });

      render(
        <FinancialEntryForm entry={existingEntry as any} />,
        { wrapper }
      );

      // Only update interest rate
      const interestRateInput = screen.getByLabelText(/interest rate/i);
      await userEvent.clear(interestRateInput);
      await userEvent.type(interestRateInput, '2.5');

      await userEvent.click(screen.getByRole('button', { name: /update liability/i }));

      // Should not send undefined fields
      await waitFor(() => {
        const callArgs = (apiClient.put as any).mock.calls[0][1];
        
        // These should be present
        expect(callArgs).toHaveProperty('interest_rate', 2.5);
        expect(callArgs).toHaveProperty('amount');
        expect(callArgs).toHaveProperty('description');
        
        // loan_start_date should not be sent if empty
        if (callArgs.loan_start_date !== undefined) {
          expect(callArgs.loan_start_date).not.toBe('');
        }
      });
    });
  });

  describe('Boolean Field Handling', () => {
    it('should correctly handle boolean fields as strings', async () => {
      (apiClient.post as any).mockResolvedValue({ success: true });

      render(<FinancialEntryForm />, { wrapper });

      await userEvent.selectOptions(screen.getByLabelText(/category/i), EntryCategory.LIABILITIES);
      await userEvent.selectOptions(screen.getByLabelText(/subcategory/i), 'mortgage_real_estate');

      // Fill required fields
      await userEvent.type(screen.getByLabelText(/description/i), 'Test');
      await userEvent.type(screen.getByLabelText(/current balance/i), '100000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '3.5');
      await userEvent.type(screen.getByLabelText(/original term/i), '30');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '20');

      // Check/uncheck boolean fields
      const fixedRateCheckbox = screen.getByLabelText(/fixed rate/i);
      if (fixedRateCheckbox) {
        await userEvent.click(fixedRateCheckbox);
      }

      await userEvent.click(screen.getByRole('button', { name: /add liability/i }));

      await waitFor(() => {
        const callArgs = (apiClient.post as any).mock.calls[0][1];
        
        // is_fixed_rate should be boolean, not string
        expect(typeof callArgs.is_fixed_rate).toBe('boolean');
        
        // Other boolean fields if present
        if (callArgs.escrow_included !== undefined) {
          expect(typeof callArgs.escrow_included).toBe('boolean');
        }
        if (callArgs.tax_deductible !== undefined) {
          expect(typeof callArgs.tax_deductible).toBe('boolean');
        }
      });
    });
  });

  describe('Authentication Error Handling', () => {
    it('should handle expired authentication gracefully', async () => {
      const authError = {
        response: {
          status: 401,
          data: {
            detail: 'Could not validate credentials',
          },
        },
      };

      (apiClient.post as any).mockRejectedValue(authError);

      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      const reloadSpy = vi.spyOn(window.location, 'reload').mockImplementation(() => {});

      render(<FinancialEntryForm />, { wrapper });

      await userEvent.selectOptions(screen.getByLabelText(/category/i), EntryCategory.LIABILITIES);
      await userEvent.selectOptions(screen.getByLabelText(/subcategory/i), 'mortgage_real_estate');

      // Fill and submit
      await userEvent.type(screen.getByLabelText(/description/i), 'Test');
      await userEvent.type(screen.getByLabelText(/current balance/i), '100000');
      await userEvent.type(screen.getByLabelText(/interest rate/i), '3.5');
      await userEvent.type(screen.getByLabelText(/original term/i), '30');
      await userEvent.type(screen.getByLabelText(/years remaining/i), '20');

      await userEvent.click(screen.getByRole('button', { name: /add liability/i }));

      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          expect.stringContaining('Your session has expired')
        );
        expect(reloadSpy).toHaveBeenCalled();
      });

      alertSpy.mockRestore();
      reloadSpy.mockRestore();
    });
  });
});