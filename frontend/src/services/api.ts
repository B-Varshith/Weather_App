/**
 * API service for communicating with the backend.
 */

export interface SOPCitation {
  id: string | null;
  name: string | null;
  severity: string | null;
}

export interface ChatResponseData {
  session_id: string;
  answer: string;
  sop: SOPCitation | null;
  weather: Record<string, any> | null;
  location: Record<string, any> | null;
  trace: Record<string, any>[];
  error: string | null;
}

const API_BASE = import.meta.env.VITE_API_URL || 'https://weather-app-u5vv.vercel.app/api';

export async function sendMessage(
  sessionId: string,
  message: string
): Promise<ChatResponseData> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
