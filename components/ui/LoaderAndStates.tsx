import React from 'react';

export const Loader: React.FC<{ size?: 'sm' | 'md' | 'lg'; label?: string; fullPage?: boolean }> = ({
  size = 'md',
  label,
  fullPage = false,
}) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-10 w-10',
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className={`${sizes[size]} animate-spin rounded-full border-2 border-gray-200 border-t-gray-900`} />
      {label && <p className="text-xs text-gray-500">{label}</p>}
    </div>
  );

  if (fullPage) {
    return <div className="flex min-h-[200px] w-full items-center justify-center">{spinner}</div>;
  }

  return spinner;
};

export const Skeleton: React.FC<{ variant?: 'card' | 'table' | 'form'; count?: number }> = ({
  variant = 'card',
  count = 3,
}) => {
  if (variant === 'card') {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-2xl border border-gray-200 bg-white p-5">
            <div className="h-4 w-3/4 rounded bg-gray-200" />
            <div className="mt-3 h-3 w-1/2 rounded bg-gray-100" />
            <div className="mt-4 flex gap-2">
              <div className="h-5 w-16 rounded-full bg-gray-100" />
              <div className="h-5 w-16 rounded-full bg-gray-100" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div className="animate-pulse space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <div className="h-8 w-full rounded bg-gray-100" />
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-12 w-full rounded bg-gray-50" />
        ))}
      </div>
    );
  }

  return (
    <div className="animate-pulse space-y-4">
      <div className="h-10 w-full rounded-lg bg-gray-200" />
      <div className="h-10 w-full rounded-lg bg-gray-100" />
      <div className="h-10 w-1/3 rounded-lg bg-gray-900" />
    </div>
  );
};

export const EmptyState: React.FC<{ title?: string; description?: string; action?: React.ReactNode }> = ({
  title = 'No leads found',
  description = 'Try changing your country or industry filters to find new businesses.',
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-gray-50/50 py-16 px-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm border">🔍</div>
      <h3 className="mt-4 text-sm font-semibold text-gray-900">{title}</h3>
      <p className="mt-1 max-w-sm text-xs text-gray-500">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

 