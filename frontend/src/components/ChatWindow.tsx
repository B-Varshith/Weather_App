import React, { useState, useRef, useEffect, useCallback } from 'react';
import Message, { MessageData } from './Message';
import ChatInput from './ChatInput';
import { sendMessage, ChatResponseData } from '../services/api';

interface ChatWindowProps {
  sessionId: string;
  onNewSession: () => void;
}

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
    // Add user message
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
      <header className="flex-shrink-0 bg-dark-800/95 backdrop-blur-sm border-b border-dark-600/50 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
              <span className="text-lg">⛅</span>
            </div>
            <div>
              <h1 className="text-base font-bold text-dark-50 tracking-tight">Weather Advisory Bot</h1>
              <p className="text-[10px] text-dark-400 font-mono">Policy-controlled safety advisor</p>
            </div>
          </div>
          <button
            id="new-session-btn"
            onClick={onNewSession}
            className="text-xs text-dark-300 hover:text-primary-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-dark-700/50"
          >
            New Session
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-16 animate-fade-in">
              <div className="text-5xl mb-4">🌦️</div>
              <h2 className="text-xl font-bold text-dark-100 mb-2">Weather Advisory Bot</h2>
              <p className="text-sm text-dark-400 max-w-md mx-auto leading-relaxed">
                Ask me about the safety or suitability of outdoor activities based on live weather conditions. 
                Every recommendation is backed by a specific policy (SOP).
              </p>
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mx-auto">
                {[
                  'Is it safe to cycle in Bhopal today?',
                  'Can I take my child to the park?',
                  'Is today good for a picnic in Delhi?',
                  'Can I walk my dog this afternoon?',
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    disabled={isLoading}
                    className="text-left text-xs text-dark-300 bg-dark-700/50 hover:bg-dark-700 border border-dark-600/30 hover:border-dark-500/50 rounded-lg px-3 py-2.5 transition-all duration-200 hover:text-dark-100"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <Message key={msg.id} message={msg} />
          ))}

          {isLoading && (
            <div className="flex justify-start animate-slide-up">
              <div className="bg-dark-700/80 border border-dark-600/40 rounded-2xl rounded-bl-md px-4 py-3 shadow-lg">
                <div className="text-[10px] font-semibold uppercase tracking-wider mb-1 text-dark-300">Advisory Bot</div>
                <div className="flex gap-1.5 py-1">
                  <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full inline-block"></span>
                  <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full inline-block"></span>
                  <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full inline-block"></span>
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
