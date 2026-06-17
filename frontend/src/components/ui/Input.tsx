import React, { forwardRef, InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error, label, ...props }, ref) => {
    return (
      <div className="w-full flex flex-col gap-2 text-left">
        {label && (
          <label 
            htmlFor={props.id}
            className="text-xs font-black uppercase opacity-60 tracking-wider pl-1"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={props.id}
          className={`w-full p-4 md:p-5 rounded-token-button bg-surface-text/5 dark:bg-navy-900 border-2 outline-none font-bold text-base md:text-lg shadow-inner transition-all placeholder:font-normal placeholder:opacity-40
            ${error 
              ? 'border-brand-danger focus:ring-4 focus:ring-brand-danger/20 text-brand-danger' 
              : 'border-transparent focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/20'
            } ${className}`}
          {...props}
        />
        {error && (
          <span className="text-brand-danger text-xs font-black pl-2 animate-slide-in-right">
            {error}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
