/**
 * WealthPath AI - Select Component
 */
import React from 'react';
import { clsx } from 'clsx';
import { ChevronDown } from 'lucide-react';

interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: Option[];
  placeholder?: string;
  fullWidth?: boolean;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  error,
  helperText,
  options,
  placeholder,
  fullWidth = true,
  className,
  id,
  ...props
}, ref) => {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={clsx('flex flex-col', fullWidth ? 'w-full' : 'w-auto')}>
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-gray-200 mb-1"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        <select
          id={selectId}
          ref={ref}
          className={clsx(
            'block w-full rounded-md border-gray-600 bg-gray-700 text-white shadow-sm transition-colors appearance-none',
            'focus:border-blue-400 focus:ring-blue-400 focus:ring-1',
            'pr-10 py-2 pl-3',
            error && 'border-red-400 focus:border-red-400 focus:ring-red-400',
            'disabled:bg-gray-600 disabled:text-gray-400',
            className
          )}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none">
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>
      
      {(error || helperText) && (
        <p className={clsx(
          'mt-1 text-xs',
          error ? 'text-red-400' : 'text-gray-300'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;