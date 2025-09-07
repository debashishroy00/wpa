/**
 * WealthPath AI - Financial Entries List Component
 */
import React, { useState } from 'react';
import { format } from 'date-fns';
import { 
  Edit3, 
  Trash2, 
  Filter, 
  Plus, 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  Calendar,
  Tag,
} from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Select from '../ui/Select';
import Input from '../ui/Input';
import { 
  FinancialEntry, 
  EntryCategory, 
  DataQuality, 
  FrequencyType,
  FinancialEntryFilters 
} from '../../types/financial';
import { 
  useFinancialEntriesQuery, 
  useDeleteFinancialEntryMutation 
} from '../../hooks/use-financial-queries';
import { useFinancialStore } from '../../stores/financial-store';

interface FinancialEntriesListProps {
  onAddEntry?: () => void;
  onEditEntry?: (entry: FinancialEntry) => void;
}

const FinancialEntriesList: React.FC<FinancialEntriesListProps> = ({
  onAddEntry,
  onEditEntry,
}) => {
  const { filters, setFilters } = useFinancialStore();
  const [searchTerm, setSearchTerm] = useState('');
  
  const { data: entries = [], isLoading, error } = useFinancialEntriesQuery(filters);
  const deleteMutation = useDeleteFinancialEntryMutation();

  // Filter options
  const categoryOptions = [
    { value: '', label: 'All Categories' },
    { value: EntryCategory.ASSETS, label: 'Assets' },
    { value: EntryCategory.LIABILITIES, label: 'Liabilities' },
    { value: EntryCategory.INCOME, label: 'Income' },
    { value: EntryCategory.EXPENSES, label: 'Expenses' },
  ];

  const dataQualityOptions = [
    { value: '', label: 'All Quality Levels' },
    { value: DataQuality.DQ1, label: 'DQ1 - Real-time API' },
    { value: DataQuality.DQ2, label: 'DQ2 - Daily Sync' },
    { value: DataQuality.DQ3, label: 'DQ3 - Verified Manual' },
    { value: DataQuality.DQ4, label: 'DQ4 - Unverified Manual' },
  ];

  // Filter entries by search term
  const filteredEntries = entries.filter((entry) =>
    entry.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (entry.subcategory && entry.subcategory.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDeleteEntry = async (entry: FinancialEntry) => {
    if (window.confirm(`Are you sure you want to delete "${entry.description}"?`)) {
      try {
        await deleteMutation.mutateAsync(parseInt(entry.id));
      } catch (error) {
        console.error('Failed to delete entry:', error);
      }
    }
  };

  const getCategoryIcon = (category: EntryCategory) => {
    switch (category) {
      case EntryCategory.ASSETS:
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case EntryCategory.LIABILITIES:
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      case EntryCategory.INCOME:
        return <DollarSign className="w-4 h-4 text-blue-600" />;
      case EntryCategory.EXPENSES:
        return <TrendingDown className="w-4 h-4 text-orange-600" />;
      default:
        return <Tag className="w-4 h-4 text-gray-600" />;
    }
  };

  const getDataQualityBadge = (dq: DataQuality) => {
    const variants = {
      [DataQuality.DQ1]: 'success' as const,
      [DataQuality.DQ2]: 'info' as const,
      [DataQuality.DQ3]: 'warning' as const,
      [DataQuality.DQ4]: 'default' as const,
    };
    return (
      <Badge variant={variants[dq]} size="sm">
        {dq}
      </Badge>
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatFrequency = (frequency: FrequencyType) => {
    const labels = {
      [FrequencyType.ONE_TIME]: 'One-time',
      [FrequencyType.DAILY]: 'Daily',
      [FrequencyType.WEEKLY]: 'Weekly',
      [FrequencyType.MONTHLY]: 'Monthly',
      [FrequencyType.QUARTERLY]: 'Quarterly',
      [FrequencyType.ANNUALLY]: 'Annual',
    };
    return labels[frequency];
  };

  if (error) {
    return (
      <Card>
        <div className="text-center py-6">
          <p className="text-red-600">Failed to load financial entries</p>
          <Button 
            variant="outline" 
            onClick={() => window.location.reload()}
            className="mt-2"
          >
            Try Again
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Financial Entries</h2>
          <p className="text-sm text-gray-600 mt-1">
            Track and manage your financial data
          </p>
        </div>
        <Button onClick={onAddEntry} leftIcon={<Plus className="w-4 h-4" />}>
          Add Entry
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Input
            placeholder="Search entries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Filter className="w-4 h-4" />}
          />
          
          <Select
            options={categoryOptions}
            value={filters.category || ''}
            onChange={(e) => setFilters({ category: e.target.value as EntryCategory || undefined })}
            placeholder="Filter by category"
          />
          
          <Select
            options={dataQualityOptions}
            value={filters.data_quality || ''}
            onChange={(e) => setFilters({ data_quality: e.target.value as DataQuality || undefined })}
            placeholder="Filter by data quality"
          />
          
          <Button
            variant="outline"
            onClick={() => {
              setFilters({});
              setSearchTerm('');
            }}
          >
            Clear Filters
          </Button>
        </div>
      </Card>

      {/* Entries List */}
      <Card padding="none">
        {isLoading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading entries...</p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="p-6 text-center">
            <p className="text-gray-600">No financial entries found</p>
            <Button 
              onClick={onAddEntry}
              className="mt-3"
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Add Your First Entry
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredEntries.map((entry) => (
              <div key={entry.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    {/* Category Icon */}
                    <div className="flex-shrink-0">
                      {getCategoryIcon(entry.category)}
                    </div>
                    
                    {/* Entry Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {entry.description}
                        </p>
                        {entry.subcategory && (
                          <Badge variant="default" size="sm">
                            {entry.subcategory}
                          </Badge>
                        )}
                        {getDataQualityBadge(entry.data_quality)}
                      </div>
                      
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-100">
                        <span className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {format(new Date(entry.entry_date), 'MMM dd, yyyy')}
                        </span>
                        <span>{formatFrequency(entry.frequency)}</span>
                        {entry.notes && (
                          <span className="truncate max-w-xs">{entry.notes}</span>
                        )}
                      </div>
                    </div>
                    
                    {/* Amount */}
                    <div className="text-right">
                      <p className={`text-sm font-semibold ${
                        entry.category === EntryCategory.ASSETS || entry.category === EntryCategory.INCOME
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}>
                        {entry.category === EntryCategory.ASSETS || entry.category === EntryCategory.INCOME ? '+' : '-'}
                        {formatCurrency(entry.amount)}
                      </p>
                      <p className="text-xs text-gray-100">
                        Confidence: {(entry.confidence_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEditEntry?.(entry)}
                      className="p-1"
                    >
                      <Edit3 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteEntry(entry)}
                      className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Summary */}
      {filteredEntries.length > 0 && (
        <Card>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-semibold text-gray-900">
                {filteredEntries.length}
              </p>
              <p className="text-sm text-gray-600">Total Entries</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-green-600">
                {filteredEntries.filter(e => 
                  e.category === EntryCategory.ASSETS || e.category === EntryCategory.INCOME
                ).length}
              </p>
              <p className="text-sm text-gray-600">Positive</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-red-600">
                {filteredEntries.filter(e => 
                  e.category === EntryCategory.LIABILITIES || e.category === EntryCategory.EXPENSES
                ).length}
              </p>
              <p className="text-sm text-gray-600">Negative</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-blue-600">
                {filteredEntries.filter(e => e.data_quality === DataQuality.DQ1).length}
              </p>
              <p className="text-sm text-gray-600">High Quality</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default FinancialEntriesList;