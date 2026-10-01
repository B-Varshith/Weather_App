import React from 'react';
import SopCitationComponent from './SopCitation';
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

function WeatherBadge({ weather }: { weather: Record<string, any> }) {
  return (
    <div id="weather-data" className="mt-3 bg-dark-800/80 rounded-lg px-4 py-3 border border-dark-600/50 animate-fade-in">
      <div className="flex items-center gap-2 mb-2">
        <span>🌤️</span>
        <span className="font-mono text-xs font-semibold tracking-wide uppercase text-primary-400">
          Weather Data
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
        {weather.temperature_c != null && (
          <div className="flex flex-col">
            <span className="text-dark-300">Temperature</span>
            <span className="font-semibold text-dark-50">{weather.temperature_c}°C</span>
          </div>
        )}
        {weather.wind_speed_kmh != null && (
          <div className="flex flex-col">
            <span className="text-dark-300">Wind</span>
            <span className="font-semibold text-dark-50">{weather.wind_speed_kmh} km/h</span>
          </div>
        )}
        {weather.precipitation_probability != null && (
          <div className="flex flex-col">
            <span className="text-dark-300">Rain Prob.</span>
            <span className="font-semibold text-dark-50">{weather.precipitation_probability}%</span>
          </div>
        )}
        {weather.precipitation_mm != null && (
          <div className="flex flex-col">
            <span className="text-dark-300">Precipitation</span>
            <span className="font-semibold text-dark-50">{weather.precipitation_mm} mm</span>
          </div>
        )}
        {weather.uv_index != null && (
          <div className="flex flex-col">
            <span className="text-dark-300">UV Index</span>
            <span className="font-semibold text-dark-50">{weather.uv_index}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      id={`message-${message.id}`}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
    >
      <div
        className={`max-w-[85%] sm:max-w-[75%] ${
          isUser
            ? 'bg-primary-700/90 text-white rounded-2xl rounded-br-md'
            : 'bg-dark-700/80 text-dark-50 rounded-2xl rounded-bl-md border border-dark-600/40'
        } px-4 py-3 shadow-lg`}
      >
        {/* Role indicator */}
        <div className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${
          isUser ? 'text-primary-200' : 'text-dark-300'
        }`}>
          {isUser ? 'You' : 'Advisory Bot'}
        </div>

        {/* Message content */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>

        {/* Weather data badge */}
        {!isUser && message.weather && <WeatherBadge weather={message.weather} />}

        {/* SOP citation */}
        {!isUser && message.sop && message.sop.id && (
          <SopCitationComponent sop={message.sop} />
        )}

        {/* Location info */}
        {!isUser && message.location && (
          <div className="mt-2 text-[10px] text-dark-400 font-mono">
            📍 {message.location.name} ({message.location.latitude?.toFixed(4)}, {message.location.longitude?.toFixed(4)})
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-[10px] mt-2 ${isUser ? 'text-primary-300' : 'text-dark-400'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
