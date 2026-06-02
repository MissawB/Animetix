import React, { ReactNode } from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  variant?: 'primary' | 'success' | 'danger' | 'warning' | 'neutral';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'neutral',
  className = '',
  ...props
}) => {
  const variants = {
    primary: 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20',
    success: 'bg-brand-success/10 text-brand-success border border-brand-success/20',
    danger: 'bg-brand-danger/10 text-brand-danger border border-brand-danger/20',
    warning: 'bg-brand-warning/10 text-brand-warning border border-brand-warning/20',
    neutral: 'bg-brand-secondary/10 text-brand-secondary border border-brand-secondary/20',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase inline-flex items-center gap-1 ${variants[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
};
