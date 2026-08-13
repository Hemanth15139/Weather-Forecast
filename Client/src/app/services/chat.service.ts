import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ChatMessage, ChatRequest, ChatResponse } from '../models/chat.model';
import { WeatherService } from './weather.service';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  // Backend LLM endpoint URL (can be customized or configured)
  private readonly apiUrl = 'http://localhost:8000/api/chat';

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

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.reply,
        timestamp: new Date()
      };
      this.messages.update((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.warn('Backend LLM API unreachable (http://localhost:8000/api/chat). Running AI simulator:', err);
      // Fallback simulated intelligent LLM response
      await this.simulateAiResponse(userMessageText);
    } finally {
      this.isTyping.set(false);
    }
  }

  clearChat(): void {
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
