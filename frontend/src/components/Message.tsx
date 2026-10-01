import React, { useState, useEffect } from 'react';
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

/* ── severity color system ────────────────────────────────── */

const severityConfig: Record<string, {
  gradient: string; border: string; text: string; dot: string;
  label: string; glow: string; iconBg: string; headerBg: string;
}> = {
  critical: {
    gradient: 'from-red-950/60 to-red-950/30',
    border: 'border-red-500/30',
    text: 'text-red-400',
    dot: 'bg-red-500',
    label: 'CRITICAL',
    glow: 'shadow-red-500/10',
    iconBg: 'bg-red-500/15',
    headerBg: 'bg-red-500/8',
  },
  high: {
    gradient: 'from-orange-950/60 to-orange-950/30',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
    dot: 'bg-orange-500',
    label: 'HIGH',
    glow: 'shadow-orange-500/10',
    iconBg: 'bg-orange-500/15',
    headerBg: 'bg-orange-500/8',
  },
  moderate: {
    gradient: 'from-amber-950/60 to-amber-950/30',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    dot: 'bg-amber-500',
    label: 'MODERATE',
    glow: 'shadow-amber-500/10',
    iconBg: 'bg-amber-500/15',
    headerBg: 'bg-amber-500/8',
  },
  low: {
    gradient: 'from-emerald-950/60 to-emerald-950/30',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    dot: 'bg-emerald-500',
    label: 'LOW',
    glow: 'shadow-emerald-500/10',
    iconBg: 'bg-emerald-500/15',
    headerBg: 'bg-emerald-500/8',
  },
};

const safeStyle = {
  gradient: 'from-emerald-950/60 to-emerald-950/30',
  border: 'border-emerald-500/30',
  text: 'text-emerald-400',
  dot: 'bg-emerald-500',
  glow: 'shadow-emerald-500/10',
  iconBg: 'bg-emerald-500/15',
  headerBg: 'bg-emerald-500/8',
};

/* ── staggered reveal hook ────────────────────────────────── */

function useStaggerReveal(count: number, baseDelay = 150) {
  const [visible, setVisible] = useState<boolean[]>(new Array(count).fill(false));

  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];
    for (let i = 0; i < count; i++) {
      timers.push(
        setTimeout(() => {
          setVisible((prev) => {
            const next = [...prev];
            next[i] = true;
            return next;
          });
        }, baseDelay * (i + 1))
      );
    }
    return () => timers.forEach(clearTimeout);
  }, [count, baseDelay]);

  return visible;
}

/* ── weather stat tile ────────────────────────────────────── */

function StatTile({ icon, label, value, unit, visible }: {
  icon: string; label: string; value: any; unit?: string; visible: boolean;
}) {
  if (value == null) return null;
  return (
    <div
      className={`
        relative overflow-hidden rounded-xl bg-gradient-to-br from-dark-800/80 to-dark-800/40
        border border-dark-600/25 p-3
        transition-all duration-500 ease-out
        ${visible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-3 scale-95'}
        hover:border-primary-500/30 hover:shadow-lg hover:shadow-primary-500/5
        group
      `}
    >
      {/* shimmer on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent
        translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700" />

      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-dark-700/80 border border-dark-600/30 flex items-center justify-center text-base flex-shrink-0">
          {icon}
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-[9px] uppercase tracking-widest text-dark-400 font-semibold leading-none mb-1">{label}</span>
          <span className="text-[15px] font-bold text-dark-50 tabular-nums leading-none">
            {value}<span className="text-dark-300 text-xs font-medium">{unit || ''}</span>
          </span>
        </div>
      </div>
    </div>
  );
}

/* ── weather card ─────────────────────────────────────────── */

function WeatherCard({ weather }: { weather: Record<string, any> }) {
  const stats = [
    { icon: '🌡️', label: 'Temperature', value: weather.temperature_c, unit: '°C' },
    { icon: '💨', label: 'Wind', value: weather.wind_speed_kmh, unit: ' km/h' },
    { icon: '🌬️', label: 'Gusts', value: weather.wind_gusts_kmh, unit: ' km/h' },
    { icon: '🌧️', label: 'Rain', value: weather.precipitation_probability, unit: '%' },
    { icon: '☔', label: 'Precip.', value: weather.precipitation_mm, unit: ' mm' },
    { icon: '☀️', label: 'UV Index', value: weather.uv_index, unit: '' },
  ].filter(s => s.value != null);

  const stagger = useStaggerReveal(stats.length, 80);

  return (
    <div className="mt-4 card-enter rounded-2xl border border-dark-600/30 bg-gradient-to-b from-dark-800/60 to-dark-800/30 overflow-hidden shadow-xl shadow-black/20 backdrop-blur-sm">
      {/* header */}
      <div className="px-4 py-3 border-b border-dark-600/20 bg-primary-500/5 flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-primary-500/15 flex items-center justify-center">
          <span className="text-sm">🌤️</span>
        </div>
        <span className="text-[11px] font-extrabold uppercase tracking-[0.15em] text-primary-400">
          Current Weather
        </span>
      </div>

      {/* stats grid */}
      <div className="p-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
        {stats.map((s, i) => (
          <StatTile key={s.label} {...s} visible={stagger[i]} />
        ))}
      </div>
    </div>
  );
}

/* ── policy triggered card ────────────────────────────────── */

function PolicyCard({ sop }: { sop: SOPCitation }) {
  const sev = severityConfig[(sop.severity || 'moderate').toLowerCase()] || severityConfig.moderate;
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 250);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={`
      mt-3 rounded-2xl border overflow-hidden shadow-xl ${sev.glow}
      bg-gradient-to-b ${sev.gradient}
      ${sev.border}
      transition-all duration-600 ease-out
      ${show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
    `}>
      {/* header */}
      <div className={`px-4 py-3 border-b ${sev.border} ${sev.headerBg} flex items-center justify-between`}>
        <div className="flex items-center gap-2.5">
          <div className={`w-7 h-7 rounded-lg ${sev.iconBg} flex items-center justify-center`}>
            <span className={`w-2.5 h-2.5 rounded-full ${sev.dot} sop-pulse`} />
          </div>
          <span className={`text-[11px] font-extrabold uppercase tracking-[0.15em] ${sev.text}`}>
            ⚠ Policy Triggered
          </span>
        </div>
        <span className={`
          text-[10px] font-black uppercase tracking-wider
          px-2.5 py-1 rounded-full border
          ${sev.border} ${sev.text}
        `}>
          {sev.label}
        </span>
      </div>

      {/* body */}
      <div className="px-4 py-3.5">
        <div className={`text-sm font-bold ${sev.text}`}>
          {sop.id} — {sop.name}
        </div>
        <div className="text-[11px] text-dark-400 mt-1.5">
          This advisory was generated because live weather conditions breached the thresholds defined in this Standard Operating Procedure.
        </div>
      </div>
    </div>
  );
}

/* ── safe to proceed card ─────────────────────────────────── */

function SafeCard() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 250);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={`
      mt-3 rounded-2xl border overflow-hidden shadow-xl ${safeStyle.glow}
      bg-gradient-to-b ${safeStyle.gradient}
      ${safeStyle.border}
      transition-all duration-600 ease-out
      ${show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
    `}>
      {/* header */}
      <div className={`px-4 py-3 border-b ${safeStyle.border} ${safeStyle.headerBg} flex items-center justify-between`}>
        <div className="flex items-center gap-2.5">
          <div className={`w-7 h-7 rounded-lg ${safeStyle.iconBg} flex items-center justify-center`}>
            <span className="text-base">✅</span>
          </div>
          <span className={`text-[11px] font-extrabold uppercase tracking-[0.15em] ${safeStyle.text}`}>
            All Clear
          </span>
        </div>
        <span className={`
          text-[10px] font-black uppercase tracking-wider
          px-2.5 py-1 rounded-full border
          ${safeStyle.border} ${safeStyle.text}
        `}>
          SAFE
        </span>
      </div>

      {/* body */}
      <div className="px-4 py-3.5">
        <div className={`text-sm font-bold ${safeStyle.text}`}>
          No safety warnings triggered
        </div>
        <div className="text-[11px] text-dark-400 mt-1.5">
          Current weather conditions do not breach any SOP thresholds for this activity. You're good to go — but conditions can change, so check again closer to the time.
        </div>
      </div>
    </div>
  );
}

/* ── location bar ─────────────────────────────────────────── */

function LocationBar({ location }: { location: Record<string, any> }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 400);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={`
      mt-3 flex items-center gap-2.5 text-[11px] text-dark-400 font-mono
      bg-dark-800/40 rounded-xl px-3.5 py-2.5 border border-dark-600/20
      transition-all duration-500 ease-out
      ${show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}
    `}>
      <span className="text-sm">📍</span>
      <span className="font-bold text-dark-200">{location.name}</span>
      <span className="text-dark-500 text-[10px]">
        ({location.latitude?.toFixed(4)}, {location.longitude?.toFixed(4)})
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
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} msg-enter`}
    >
      {/* bot avatar */}
      {!isUser && (
        <div className="flex-shrink-0 mr-2.5 mt-1">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20 text-sm">
            ⛅
          </div>
        </div>
      )}

      <div
        className={`max-w-[85%] sm:max-w-[78%] ${
          isUser
            ? 'bg-gradient-to-br from-primary-600/95 to-primary-700/95 text-white rounded-2xl rounded-br-sm shadow-xl shadow-primary-700/20'
            : 'bg-dark-700/70 text-dark-50 rounded-2xl rounded-bl-sm border border-dark-600/30 shadow-xl shadow-black/20 backdrop-blur-sm'
        } px-4 py-3.5`}
      >
        {/* Role indicator */}
        <div className={`text-[10px] font-extrabold uppercase tracking-[0.15em] mb-2 ${
          isUser ? 'text-primary-200/80' : 'text-dark-400'
        }`}>
          {isUser ? 'You' : 'Advisory Bot'}
        </div>

        {/* Message content */}
        <div className="text-[13px] leading-relaxed">
          <ReactMarkdown
            components={{
              p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-outside ml-4 mb-2 space-y-1" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-outside ml-4 mb-2 space-y-1" {...props} />,
              li: ({ node, ...props }) => <li className="text-dark-200" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold text-dark-50" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Structured data cards */}
        {hasWeather && <WeatherCard weather={message.weather!} />}
        {hasSop && <PolicyCard sop={message.sop!} />}
        {noSopButHasWeather && <SafeCard />}
        {!isUser && message.location && <LocationBar location={message.location} />}

        {/* Timestamp */}
        <div className={`text-[10px] mt-3 ${isUser ? 'text-primary-300/70' : 'text-dark-500'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>

      {/* user avatar */}
      {isUser && (
        <div className="flex-shrink-0 ml-2.5 mt-1">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-dark-500 to-dark-600 flex items-center justify-center shadow-lg text-sm">
            👤
          </div>
        </div>
      )}
    </div>
  );
}
