import React, { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [isLoading]);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div id="chat-input" className="border-t border-dark-600/50 bg-dark-800/95 backdrop-blur-sm p-4">
      <div className="max-w-3xl mx-auto flex gap-3 items-end">
        <textarea
          ref={inputRef}
          id="message-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about outdoor activities... (e.g., Is it safe to cycle in Bhopal today?)"
          disabled={isLoading}
          rows={1}
          className="flex-1 resize-none bg-dark-700 border border-dark-500/50 rounded-xl px-4 py-3 text-sm text-dark-50 placeholder-dark-400 focus:outline-none focus:border-primary-500/60 focus:ring-1 focus:ring-primary-500/30 transition-all duration-200 disabled:opacity-50"
          style={{ minHeight: '44px', maxHeight: '120px' }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = Math.min(target.scrollHeight, 120) + 'px';
          }}
        />
        <button
          id="send-button"
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          className="flex-shrink-0 bg-primary-600 hover:bg-primary-500 disabled:bg-dark-600 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 text-sm font-semibold transition-all duration-200 shadow-lg hover:shadow-primary-600/25 active:scale-95"
        >
          {isLoading ? (
            <span className="flex gap-1">
              <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full inline-block"></span>
              <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full inline-block"></span>
              <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full inline-block"></span>
            </span>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </div>
  );
}
