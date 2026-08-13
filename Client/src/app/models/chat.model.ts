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
  suggestions?: string[];
  weather_recommendation?: string;
}
