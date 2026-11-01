import React from 'react';
import { StatusBadge } from './StatusBadge';

interface AppCardProps {
  name: string;
  address: string;
  country: string;
  whatsappStatus: 'FOUND' | 'NOT_FOUND' | 'UNKNOWN';
  chatbotStatus: 'FOUND' | 'NOT_FOUND' | 'UNKNOWN';
  leadScore?: 'HIGH' | 'MEDIUM' | 'LOW';
  onView?: () => void;
}

export const AppCard: React.FC<AppCardProps> = ({
  name,
  address,
  country,
  whatsappStatus,
  chatbotStatus,
  leadScore = 'MEDIUM',
  onView,
}) => {
  const isHighLead = leadScore === 'HIGH';
  const isLowLead = leadScore === 'LOW';

  return (
    <div
      className={`
        relative rounded-2xl border bg-white p-5 transition-all hover:shadow-md
        ${isHighLead ? 'border-amber-200 bg-amber-50/30 shadow-sm' : 'border-gray-200'}
        ${isLowLead ? 'opacity-70' : ''}
      `}
    >
      {isHighLead && (
        <div className="absolute -top-2.5 left-5 rounded-full bg-amber-500 px-2.5 py-0.5 text-[10px] font-bold text-white">
          HIGH POTENTIAL LEAD
        </div>
      )}

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-1">{name}</h3>
          <p className="mt-1 text-xs text-gray-500">{address} • {country}</p>
        </div>
        <div className={`h-2 w-2 rounded-full ${isHighLead ? 'bg-amber-400' : isLowLead ? 'bg-gray-300' : 'bg-blue-500'}`} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge status={whatsappStatus} variant="whatsapp" label="WhatsApp" size="sm" />
        <StatusBadge status={chatbotStatus} variant="chatbot" label="Chatbot" size="sm" />
      </div>

      {onView && (
        <button
          onClick={onView}
          className="mt-4 w-full rounded-lg border border-gray-200 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          View Details
        </button>
      )}
    </div>
  );
};

 