import React from 'react';
import ReactMarkdown from 'react-markdown';
import { SOPCitation } from '../services/api';

export interface MessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sop?: SOPCitation | null;
  weather?: Record<string, any> | null;
  location?: Record<string, any> | null;
  error?: string | null;
  timestamp: Date;
}

interface MessageProps {
  message: MessageData;
}

/* ── severity helpers ─────────────────────────────────────── */

const severityConfig: Record<string, { bg: string; border: string; text: string; dot: string; label: string }> = {
  critical: { bg: 'bg-red-950/40',    border: 'border-red-500/40',    text: 'text-red-400',    dot: 'bg-red-500',    label: 'CRITICAL' },
  high:     { bg: 'bg-orange-950/40',  border: 'border-orange-500/40', text: 'text-orange-400', dot: 'bg-orange-500', label: 'HIGH' },
  moderate: { bg: 'bg-amber-950/40',   border: 'border-amber-500/40',  text: 'text-amber-400',  dot: 'bg-amber-500',  label: 'MODERATE' },
  low:      { bg: 'bg-emerald-950/40', border: 'border-emerald-500/40',text: 'text-emerald-400',dot: 'bg-emerald-500',label: 'LOW' },
};

const safeConfig = { bg: 'bg-emerald-950/40', border: 'border-emerald-500/40', text: 'text-emerald-400', dot: 'bg-emerald-500', label: 'SAFE' };

function getSeverity(sop: SOPCitation | null | undefined) {
  if (!sop?.severity) return null;
  return severityConfig[sop.severity.toLowerCase()] || severityConfig.moderate;
}

/* ── weather stat pill ────────────────────────────────────── */

function Stat({ icon, label, value, unit }: { icon: string; label: string; value: any; unit?: string }) {
  if (value == null) return null;
  return (
    <div className="flex items-center gap-2.5 bg-dark-800/60 rounded-lg px-3 py-2.5 border border-dark-600/30">
      <span className="text-base flex-shrink-0">{icon}</span>
      <div className="flex flex-col min-w-0">
        <span className="text-[10px] uppercase tracking-wider text-dark-400 font-medium">{label}</span>
        <span className="text-sm font-semibold text-dark-50 tabular-nums">
          {value}{unit || ''}
        </span>
      </div>
    </div>
  );
}

/* ── weather card ─────────────────────────────────────────── */

function WeatherCard({ weather }: { weather: Record<string, any> }) {
  return (
    <div className="mt-3 rounded-xl border border-dark-600/40 bg-dark-800/50 overflow-hidden animate-fade-in">
      <div className="px-4 py-2.5 border-b border-dark-600/30 flex items-center gap-2">
        <span className="text-sm">🌤️</span>
        <span className="text-[11px] font-bold uppercase tracking-widest text-primary-400">Current Weather</span>
      </div>
      <div className="p-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
        <Stat icon="🌡️" label="Temperature" value={weather.temperature_c} unit="°C" />
        <Stat icon="💨" label="Wind" value={weather.wind_speed_kmh} unit=" km/h" />
        <Stat icon="🌧️" label="Rain Prob." value={weather.precipitation_probability} unit="%" />
        <Stat icon="☔" label="Precipitation" value={weather.precipitation_mm} unit=" mm" />
        <Stat icon="☀️" label="UV Index" value={weather.uv_index} />
        {weather.wind_gusts_kmh != null && (
          <Stat icon="🌬️" label="Wind Gusts" value={weather.wind_gusts_kmh} unit=" km/h" />
        )}
      </div>
    </div>
  );
}

/* ── policy card ──────────────────────────────────────────── */

function PolicyCard({ sop }: { sop: SOPCitation }) {
  const sev = getSeverity(sop);
  if (!sev) return null;

  return (
    <div className={`mt-3 rounded-xl border overflow-hidden animate-fade-in ${sev.border} ${sev.bg}`}>
      <div className={`px-4 py-2.5 border-b ${sev.border} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${sev.dot} animate-pulse-soft`} />
          <span className={`text-[11px] font-bold uppercase tracking-widest ${sev.text}`}>Policy Applied</span>
        </div>
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${sev.border} ${sev.text}`}>
          {sev.label}
        </span>
      </div>
      <div className="px-4 py-3">
        <div className={`text-sm font-bold ${sev.text}`}>
          {sop.id} — {sop.name}
        </div>
      </div>
    </div>
  );
}

/* ── safe-to-proceed card (no SOP matched) ────────────────── */

function SafeCard() {
  return (
    <div className={`mt-3 rounded-xl border overflow-hidden animate-fade-in ${safeConfig.border} ${safeConfig.bg}`}>
      <div className={`px-4 py-2.5 border-b ${safeConfig.border} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${safeConfig.dot}`} />
          <span className={`text-[11px] font-bold uppercase tracking-widest ${safeConfig.text}`}>Policy Check</span>
        </div>
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${safeConfig.border} ${safeConfig.text}`}>
          {safeConfig.label}
        </span>
      </div>
      <div className="px-4 py-3">
        <div className={`text-sm font-semibold ${safeConfig.text}`}>
          No safety warnings triggered — safe to proceed
        </div>
        <div className="text-xs text-dark-400 mt-1">
          Current weather conditions do not match any cautionary SOPs for this activity.
        </div>
      </div>
    </div>
  );
}

/* ── location footer ──────────────────────────────────────── */

function LocationFooter({ location }: { location: Record<string, any> }) {
  return (
    <div className="mt-3 flex items-center gap-2 text-[11px] text-dark-400 font-mono bg-dark-800/30 rounded-lg px-3 py-2 border border-dark-600/20">
      <span className="text-xs">📍</span>
      <span className="font-semibold text-dark-300">{location.name}</span>
      <span className="text-dark-500">
        {location.latitude?.toFixed(4)}, {location.longitude?.toFixed(4)}
      </span>
    </div>
  );
}

/* ── main Message component ───────────────────────────────── */

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';
  const hasSop = !isUser && message.sop && message.sop.id;
  const hasWeather = !isUser && message.weather;
  const noSopButHasWeather = !isUser && hasWeather && !hasSop && !message.error;

  return (
    <div
      id={`message-${message.id}`}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
    >
      <div
        className={`max-w-[88%] sm:max-w-[80%] ${
          isUser
            ? 'bg-primary-700/90 text-white rounded-2xl rounded-br-md'
            : 'bg-dark-700/80 text-dark-50 rounded-2xl rounded-bl-md border border-dark-600/40'
        } px-4 py-3 shadow-lg`}
      >
        {/* Role indicator */}
        <div className={`text-[10px] font-bold uppercase tracking-widest mb-1.5 ${
          isUser ? 'text-primary-200' : 'text-dark-400'
        }`}>
          {isUser ? 'You' : '⛅ Advisory Bot'}
        </div>

        {/* Message content */}
        <div className="text-sm leading-relaxed">
          <ReactMarkdown
            components={{
              p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-outside ml-4 mb-2 space-y-1" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-outside ml-4 mb-2 space-y-1" {...props} />,
              li: ({ node, ...props }) => <li className="text-dark-200" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold text-dark-50" {...props} />,
              h1: ({ node, ...props }) => <h1 className="text-base font-bold text-dark-50 mb-2" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-sm font-bold text-dark-100 mt-3 mb-1.5" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-sm font-semibold text-dark-200 mt-2 mb-1" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Structured data cards — rendered from API data, not LLM text */}
        {hasWeather && <WeatherCard weather={message.weather!} />}
        {hasSop && <PolicyCard sop={message.sop!} />}
        {noSopButHasWeather && <SafeCard />}
        {!isUser && message.location && <LocationFooter location={message.location} />}

        {/* Timestamp */}
        <div className={`text-[10px] mt-2.5 ${isUser ? 'text-primary-300' : 'text-dark-500'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
