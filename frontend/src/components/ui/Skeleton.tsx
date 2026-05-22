import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  className = '', 
  variant = 'rectangular' 
}) => {
  const baseStyles = 'animate-pulse bg-gray-200 dark:bg-navy-700';
  
  const variants = {
    text: 'h-4 w-full rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-2xl',
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${className}`} />
  );
};

export const CardSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-navy-800 rounded-[3rem] p-10 shadow-2xl border border-gray-100 dark:border-white/5 w-full max-w-3xl mx-auto">
    <div className="flex flex-col items-center gap-6">
      <Skeleton variant="circular" className="w-16 h-16" />
      <Skeleton variant="text" className="h-8 w-1/2 mb-4" />
      <Skeleton className="h-32 w-full rounded-3xl" />
      <div className="w-full space-y-4 mt-6">
        <Skeleton variant="text" className="h-12 w-full" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      </div>
    </div>
  </div>
);
