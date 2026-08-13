import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WeatherService } from './services/weather.service';
import { WeatherCardComponent } from './components/weather-card/weather-card.component';
import { WeatherMetricsComponent } from './components/weather-metrics/weather-metrics.component';
import { ForecastTimelineComponent } from './components/forecast-timeline/forecast-timeline.component';
import { ChatbotComponent } from './components/chatbot/chatbot.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    WeatherCardComponent,
    WeatherMetricsComponent,
    ForecastTimelineComponent,
    ChatbotComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  // View mode switcher: 'split' | 'weather' | 'chat'
  readonly activeView = signal<'split' | 'weather' | 'chat'>('split');

  // Dynamic Backdrop Theme Gradient based on Weather Condition & Light/Dark Mode
  readonly backgroundTheme = computed(() => {
    const isLight = this.weatherService.theme() === 'light';
    const data = this.weatherService.weatherData();

    if (isLight) {
      if (!data) return 'from-sky-100 via-blue-50 to-slate-100';
      const cond = data.current.condition.toLowerCase();
      if (cond.includes('clear') || cond.includes('sun')) {
        return 'from-sky-100 via-sky-200/60 to-blue-100'; // Light Sunny
      } else if (cond.includes('rain') || cond.includes('drizzle')) {
        return 'from-slate-100 via-cyan-100 to-slate-200'; // Light Rainy
      } else if (cond.includes('thunder') || cond.includes('storm')) {
        return 'from-indigo-100 via-purple-100 to-slate-200'; // Light Storm
      }
      return 'from-slate-100 via-blue-100/50 to-slate-200'; // Light Overcast
    }

    // Dark Mode Gradients
    if (!data) return 'from-slate-950 via-slate-900 to-slate-950';

    const cond = data.current.condition.toLowerCase();
    const isDay = data.current.isDay;

    if (!isDay) {
      return 'from-slate-950 via-indigo-950 to-slate-900'; // Night starry
    }

    if (cond.includes('clear') || cond.includes('sun')) {
      return 'from-slate-950 via-sky-950 to-blue-950'; // Bright Sunny
    } else if (cond.includes('rain') || cond.includes('drizzle')) {
      return 'from-slate-950 via-cyan-950 to-slate-900'; // Rainy
    } else if (cond.includes('thunder') || cond.includes('storm')) {
      return 'from-slate-950 via-purple-950 to-slate-950'; // Thunderstorm
    } else if (cond.includes('snow')) {
      return 'from-slate-950 via-slate-900 to-sky-950'; // Snow
    }

    return 'from-slate-950 via-slate-900 to-indigo-950'; // Default Cloud / Overcast
  });


  constructor(public weatherService: WeatherService) {}
}
