import React from 'react';
import { SOPCitation } from '../services/api';

interface SopCitationProps {
  sop: SOPCitation;
}

const severityColors: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  moderate: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
};

const severityIcons: Record<string, string> = {
  critical: '🔴',
  high: '🟠',
  moderate: '🟡',
  low: '🟢',
};

export default function SopCitationComponent({ sop }: SopCitationProps) {
  if (!sop.id) return null;

  const severity = sop.severity?.toLowerCase() || 'moderate';
  const colorClass = severityColors[severity] || severityColors.moderate;
  const icon = severityIcons[severity] || '⚪';

  return (
    <div
      id="sop-citation"
      className={`mt-3 rounded-lg border px-4 py-3 ${colorClass} animate-fade-in`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm">{icon}</span>
        <span className="font-mono text-xs font-semibold tracking-wide uppercase">
          Policy Applied
        </span>
      </div>
      <div className="font-semibold text-sm">
        {sop.id} — {sop.name}
      </div>
      <div className="text-xs mt-1 opacity-80">
        Severity: <span className="font-semibold uppercase">{sop.severity}</span>
      </div>
    </div>
  );
}
