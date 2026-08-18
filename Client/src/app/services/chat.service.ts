import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ChatMessage, ChatRequest, ChatResponse } from '../models/chat.model';
import { WeatherService } from './weather.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  // Backend LLM endpoint URL with environment and production fallbacks
  private readonly apiUrl = (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')
    ? (environment.apiUrl || '/api/chat')
    : (environment.apiUrl || 'http://localhost:8000/api/chat');
  private sessionId: string = (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : Date.now().toString();

  readonly messages = signal<ChatMessage[]>([
    {
      id: 'welcome-msg',
      sender: 'assistant',
      text: "👋 Hi! I'm your AI Weather Assistant powered by LLM. Ask me anything about the forecast, packing advice, travel plans, outdoor activities, or severe weather alerts!",
      timestamp: new Date()
    }
  ]);

  readonly isTyping = signal<boolean>(false);
  readonly isVoiceActive = signal<boolean>(false);

  constructor(
    private http: HttpClient,
    private weatherService: WeatherService
  ) {}

  async sendMessage(text: string): Promise<void> {
    if (!text || !text.trim() || this.isTyping()) return;

    const userMessageText = text.trim();
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: userMessageText,
      timestamp: new Date()
    };

    // Add user message to stream
    this.messages.update((prev) => [...prev, userMsg]);
    this.isTyping.set(true);

    const weatherData = this.weatherService.weatherData();
    const currentLoc = this.weatherService.selectedLocation();

    const requestPayload: ChatRequest = {
      message: userMessageText,
      session_id: this.sessionId,
      location: currentLoc.name,
      current_weather: weatherData
        ? {
            temp: weatherData.current.tempC,
            condition: weatherData.current.condition,
            humidity: weatherData.current.humidity,
            wind_speed: weatherData.current.windSpeedKmH
          }
        : undefined
    };

    try {
      // Attempt call to LLM API backend
      const response = await firstValueFrom(
        this.http.post<ChatResponse>(this.apiUrl, requestPayload)
      );

      if (response.session_id) {
        this.sessionId = response.session_id;
      }

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.reply,
        timestamp: new Date(),
        weatherSnapshot: response.weather_snapshot ? {
          location: response.weather_snapshot.location,
          temp: response.weather_snapshot.temp,
          condition: response.weather_snapshot.condition,
          humidity: response.weather_snapshot.humidity,
          recommendation: response.weather_snapshot.recommendation
        } : undefined
      };
      this.messages.update((prev) => [...prev, aiMsg]);

      const targetLoc = response.location ? {
        name: response.location.name,
        country: response.location.country || '',
        latitude: response.location.latitude,
        longitude: response.location.longitude
      } : this.weatherService.selectedLocation();

      if (response.target_date || response.target_time) {
        this.weatherService.setLocationWithTarget(
          targetLoc,
          response.target_date,
          response.target_time,
          response.target_label
        );
      } else if (response.location) {
        this.weatherService.setLocation(targetLoc);
      }
    } catch (err) {
      console.warn('Backend LLM API unreachable (http://localhost:8000/api/chat). Running AI simulator:', err);
      // Fallback simulated intelligent LLM response
      await this.simulateAiResponse(userMessageText);
    } finally {
      this.isTyping.set(false);
    }
  }

  clearChat(): void {
    this.sessionId = (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : Date.now().toString();
    this.messages.set([
      {
        id: Date.now().toString(),
        sender: 'assistant',
        text: "Chat cleared! How can I assist you with your weather forecast today?",
        timestamp: new Date()
      }
    ]);
  }

  toggleVoice(): void {
    this.isVoiceActive.set(!this.isVoiceActive());
  }

  private async simulateAiResponse(query: string): Promise<void> {
    const q = query.toLowerCase();
    const weather = this.weatherService.weatherData();
    const locationName = this.weatherService.selectedLocation().name;
    const temp = weather ? `${weather.current.tempC}°C (${weather.current.tempF}°F)` : '24°C';
    const condition = weather ? weather.current.condition : 'Partly Cloudy';
    const humidity = weather ? `${weather.current.humidity}%` : '58%';
    const wind = weather ? `${weather.current.windSpeedKmH} km/h` : '14 km/h';

    let reply = '';
    let snapshot;

    if (q.includes('wear') || q.includes('outfit') || q.includes('clothes')) {
      reply = `Based on current conditions in **${locationName}** (${temp}, ${condition}), I recommend a comfortable layer—like a light breathable jacket or hoodie for the evening. Don't forget sunglasses if it brightens up!`;
      snapshot = {
        location: locationName,
        temp,
        condition,
        humidity,
        recommendation: 'Light outfit & comfortable sneakers'
      };
    } else if (q.includes('rain') || q.includes('umbrella') || q.includes('shower')) {
      const pop = weather?.hourly[0]?.pop ?? 15;
      reply = pop > 40
        ? `🌧️ Yes, there is a **${pop}% chance of rain** today in **${locationName}**. It's best to keep a compact umbrella or rain jacket handy!`
        : `☀️ Precipitation risk in **${locationName}** is quite low right now (around **${pop}%**). You should be safe without an umbrella!`;
    } else if (q.includes('travel') || q.includes('trip') || q.includes('pack')) {
      reply = `✈️ Planning a trip to **${locationName}**? Expect temperatures around **${temp}** with **${condition}** skies. High humidity is around **${humidity}**. Pack light cotton clothes, sun protection, and a versatile outer shell.`;
    } else if (q.includes('run') || q.includes('outdoor') || q.includes('exercise') || q.includes('air')) {
      const aqi = weather?.metrics.airQualityIndex ?? 35;
      const status = weather?.metrics.airQualityLabel ?? 'Good';
      reply = `🏃 Air quality in **${locationName}** is **${status}** (AQI: ${aqi}). It's a great time for outdoor workouts, running, or cycling!`;
    } else {
      reply = `🌤️ In **${locationName}**, it's currently **${temp}** with **${condition}**. Humidity stands at **${humidity}** and wind speeds are around **${wind}**. Let me know if you need specific advice on evening plans or 7-day outlooks!`;
    }

    // Typing effect simulation
    await new Promise((resolve) => setTimeout(resolve, 800));

    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'assistant',
      text: reply,
      timestamp: new Date(),
      weatherSnapshot: snapshot
    };

    this.messages.update((prev) => [...prev, aiMsg]);
  }
}
