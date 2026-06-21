import React, { ButtonHTMLAttributes, ElementType } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  as?: ElementType;
  to?: string; // Pour supporter Link
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  fullWidth = false, 
  className = '',
  as: Component = 'button',
  ...props 
}) => {
  const baseStyles = 'font-black rounded-token-button transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-brand-primary hover:bg-brand-primary/90 text-white',
    secondary: 'bg-brand-secondary hover:bg-brand-secondary/90 text-white',
    danger: 'bg-brand-danger hover:bg-brand-danger/90 text-white',
    success: 'bg-brand-success hover:bg-brand-success/90 text-white',
    outline: 'border-2 border-surface-text/20 hover:bg-surface-text/10 text-surface-text bg-transparent',
    ghost: 'bg-transparent hover:bg-black/5 dark:hover:bg-white/10 text-current',
  };

  const sizes = {
    sm: 'py-2 px-4 text-xs',
    md: 'py-4 px-6 text-base',
    lg: 'py-5 px-8 text-lg',
  };

  return (
    <Component 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
};

