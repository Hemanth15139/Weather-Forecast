export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: Date;
  weatherSnapshot?: {
    location: string;
    temp: string;
    condition: string;
    humidity: string;
    recommendation?: string;
  };
  isStreaming?: boolean;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  location?: string;
  current_weather?: {
    temp: number;
    condition: string;
    humidity: number;
    wind_speed: number;
  };
  chat_history?: { role: string; content: string }[];
}

export interface ChatResponse {
  reply: string;
  session_id?: string;
  target_date?: string;
  target_time?: string;
  target_label?: string;
  suggestions?: string[];
  weather_recommendation?: string;
  weather_snapshot?: {
    location: string;
    temp: string;
    condition: string;
    humidity: string;
    recommendation?: string;
  };
  location?: {
    name: string;
    country?: string;
    latitude: number;
    longitude: number;
  };
}

