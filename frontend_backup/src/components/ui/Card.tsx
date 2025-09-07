/**
 * WealthPath AI - Card Component
 */
import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

interface CardComponent extends React.FC<CardProps> {
  Header: React.FC<CardHeaderProps>;
  Title: React.FC<CardTitleProps>;
  Content: React.FC<CardContentProps>;
  Body: React.FC<CardBodyProps>;
}

const Card: CardComponent = ({
  children,
  className,
  padding = 'md',
  shadow = 'md',
  hover = false,
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const shadowStyles = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  };

  return (
    <div
      className={clsx(
        'bg-gray-800 rounded-lg border border-gray-700 text-gray-100',
        paddingStyles[padding],
        shadowStyles[shadow],
        hover && 'transition-shadow hover:shadow-lg',
        className
      )}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => (
  <div className={clsx('mb-4', className)}>{children}</div>
);

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

const CardTitle: React.FC<CardTitleProps> = ({ children, className }) => (
  <h3 className={clsx('text-lg font-semibold text-gray-100', className)}>
    {children}
  </h3>
);

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

const CardContent: React.FC<CardContentProps> = ({ children, className }) => (
  <div className={className}>{children}</div>
);

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

const CardBody: React.FC<CardBodyProps> = ({ children, className }) => (
  <div className={className}>{children}</div>
);

(Card as CardComponent).Header = CardHeader;
(Card as CardComponent).Title = CardTitle;
(Card as CardComponent).Content = CardContent;
(Card as CardComponent).Body = CardBody;

export default Card;