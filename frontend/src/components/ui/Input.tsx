/**
 * WealthPath AI - Input Component
 */
import React from 'react';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  fullWidth = true,
  className,
  id,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={clsx('flex flex-col', fullWidth ? 'w-full' : 'w-auto')}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-200 mb-1"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            {leftIcon}
          </div>
        )}
        
        <input
          id={inputId}
          ref={ref}
          className={clsx(
            'block w-full rounded-md border-gray-600 bg-gray-700 text-white shadow-sm transition-colors',
            'focus:border-blue-400 focus:ring-blue-400 focus:ring-1',
            'placeholder:text-gray-400',
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            error && 'border-red-400 focus:border-red-400 focus:ring-red-400',
            'disabled:bg-gray-600 disabled:text-gray-400',
            className
          )}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            {rightIcon}
          </div>
        )}
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

Input.displayName = 'Input';

export default Input;