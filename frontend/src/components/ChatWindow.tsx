import React, { useState, useRef, useEffect, useCallback } from 'react';
import Message, { MessageData } from './Message';
import ChatInput from './ChatInput';
import { sendMessage, ChatResponseData } from '../services/api';

interface ChatWindowProps {
  sessionId: string;
  onNewSession: () => void;
}

const EXAMPLE_QUERIES = [
  { icon: '🚴', text: 'Is it safe to cycle in Bhopal today?' },
  { icon: '🧒', text: 'Can I take my child to the park in Delhi?' },
  { icon: '🧺', text: 'Is today good for a picnic in Mumbai?' },
  { icon: '🐕', text: 'Can I walk my dog this afternoon in Bangalore?' },
  { icon: '🥾', text: 'Is hiking safe in Shimla today?' },
  { icon: '🏊', text: 'Can I go swimming in Goa today?' },
];

export default function ChatWindow({ sessionId, onNewSession }: ChatWindowProps) {
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async (text: string) => {
    const userMsg: MessageData = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response: ChatResponseData = await sendMessage(sessionId, text);

      const botMsg: MessageData = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sop: response.sop,
        weather: response.weather,
        location: response.location,
        error: response.error,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorMsg: MessageData = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I encountered a network error. Please check that the backend is running and try again.',
        error: 'NETWORK_ERROR',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div id="chat-window" className="flex flex-col h-full">
      {/* Header */}
      <header className="flex-shrink-0 bg-dark-800/95 backdrop-blur-md border-b border-dark-600/50 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
              <span className="text-lg">⛅</span>
            </div>
            <div>
              <h1 className="text-base font-bold text-dark-50 tracking-tight">Weather Advisory Bot</h1>
              <p className="text-[10px] text-dark-400 font-mono tracking-wide">
                SOP-driven · Policy-controlled · No guesswork
              </p>
            </div>
          </div>
          <button
            id="new-session-btn"
            onClick={() => {
              setMessages([]);
              onNewSession();
            }}
            className="text-xs text-dark-300 hover:text-primary-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-dark-700/50 border border-dark-600/30 hover:border-dark-500/50"
          >
            + New Session
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12 animate-fade-in">
              <div className="text-6xl mb-5">🌦️</div>
              <h2 className="text-xl font-bold text-dark-100 mb-2">Weather Advisory Bot</h2>
              <p className="text-sm text-dark-400 max-w-md mx-auto leading-relaxed mb-2">
                Ask about the safety of outdoor activities based on <strong className="text-dark-300">live weather data</strong> and <strong className="text-dark-300">Standard Operating Procedures</strong>.
              </p>
              <p className="text-xs text-dark-500 max-w-sm mx-auto mb-8">
                Every recommendation is backed by a specific policy. If no policy covers your situation, the bot will tell you honestly.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-w-2xl mx-auto">
                {EXAMPLE_QUERIES.map((q) => (
                  <button
                    key={q.text}
                    onClick={() => handleSend(q.text)}
                    disabled={isLoading}
                    className="group text-left text-xs text-dark-300 bg-dark-800/60 hover:bg-dark-700/80 border border-dark-600/30 hover:border-primary-500/30 rounded-xl px-4 py-3 transition-all duration-200 hover:text-dark-100 hover:shadow-lg hover:shadow-primary-500/5"
                  >
                    <span className="text-base mr-2">{q.icon}</span>
                    <span className="group-hover:text-dark-50 transition-colors">{q.text}</span>
                  </button>
                ))}
              </div>

              <div className="mt-10 flex items-center justify-center gap-4 text-[10px] text-dark-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Safe conditions
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  Use caution
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                  High risk
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                  Critical
                </span>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <Message key={msg.id} message={msg} />
          ))}

          {isLoading && (
            <div className="flex justify-start msg-enter">
              <div className="flex-shrink-0 mr-2.5 mt-1">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20 text-sm animate-pulse-soft">
                  ⛅
                </div>
              </div>
              <div className="bg-dark-700/70 border border-dark-600/30 rounded-2xl rounded-bl-sm px-5 py-4 shadow-xl shadow-black/20 backdrop-blur-sm">
                <div className="text-[10px] font-extrabold uppercase tracking-[0.15em] mb-2.5 text-dark-400">Advisory Bot</div>
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full inline-block"></span>
                    <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full inline-block"></span>
                    <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full inline-block"></span>
                  </div>
                  <span className="text-[10px] text-dark-500 font-medium">Checking weather & evaluating SOPs…</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}
