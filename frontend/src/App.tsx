import React, { useState, useCallback } from 'react';
import ChatWindow from './components/ChatWindow';

function generateSessionId(): string {
  // Simple UUID v4 generator
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function App() {
  const [sessionId, setSessionId] = useState<string>(generateSessionId());

  const handleNewSession = useCallback(() => {
    setSessionId(generateSessionId());
  }, []);

  return (
    <div id="app" className="h-screen bg-dark-900">
      <ChatWindow sessionId={sessionId} onNewSession={handleNewSession} />
    </div>
  );
}
