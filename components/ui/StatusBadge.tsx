import React from 'react';

type BadgeStatus = 'FOUND' | 'NOT_FOUND' | 'UNKNOWN';
type BadgeVariant = 'whatsapp' | 'chatbot' | 'generic';

interface StatusBadgeProps {
  status: BadgeStatus;
  variant?: BadgeVariant;
  label?: string;
  size?: 'sm' | 'md';
}

const statusConfig = {
  FOUND: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    dot: 'bg-emerald-500',
    defaultLabel: 'Available',
  },
  NOT_FOUND: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-200',
    dot: 'bg-red-500',
    defaultLabel: 'Not Found',
  },
  UNKNOWN: {
    bg: 'bg-gray-50',
    text: 'text-gray-600',
    border: 'border-gray-200',
    dot: 'bg-gray-400',
    defaultLabel: 'Unknown',
  },
};

const variantIcons = {
  whatsapp: '💬',
  chatbot: '🤖',
  generic: '●',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'generic',
  label,
  size = 'md',
}) => {
  const config = statusConfig[status];
  const isSmall = size === 'sm';

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full border font-medium
        ${config.bg} ${config.text} ${config.border}
        ${isSmall ? 'px-2.5 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'}
        transition-colors
      `}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {variant !== 'generic' && (
        <span className="text-[11px]">{variantIcons[variant]}</span>
      )}
      <span>{label || config.defaultLabel}</span>
    </span>
  );
};
