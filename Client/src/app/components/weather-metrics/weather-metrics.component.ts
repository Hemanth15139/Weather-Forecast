import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WeatherService } from '../../services/weather.service';

@Component({
  selector: 'app-weather-metrics',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (weatherService.weatherData(); as data) {
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        
        <!-- Air Quality Card -->
        <div class="glass-card p-4 rounded-2xl flex flex-col justify-between group hover:border-emerald-500/30 transition-all">
          <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Air Quality</span>
            <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
          </div>

          <div class="my-3">
            <div class="text-2xl font-extrabold text-white">
              {{ data.metrics.airQualityIndex }} <span class="text-xs font-normal text-slate-400">AQI</span>
            </div>
            <div class="mt-1">
              <span
                class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase"
                [ngClass]="{
                  'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': data.metrics.airQualityIndex <= 50,
                  'bg-amber-500/20 text-amber-300 border border-amber-500/30': data.metrics.airQualityIndex > 50 && data.metrics.airQualityIndex <= 100,
                  'bg-rose-500/20 text-rose-300 border border-rose-500/30': data.metrics.airQualityIndex > 100
                }"
              >
                {{ data.metrics.airQualityLabel }}
              </span>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              [style.width.%]="mathMin((data.metrics.airQualityIndex / 150) * 100, 100)"
              [ngClass]="{
                'bg-emerald-400': data.metrics.airQualityIndex <= 50,
                'bg-amber-400': data.metrics.airQualityIndex > 50 && data.metrics.airQualityIndex <= 100,
                'bg-rose-500': data.metrics.airQualityIndex > 100
              }"
            ></div>
          </div>
        </div>

        <!-- Wind Card -->
        <div class="glass-card p-4 rounded-2xl flex flex-col justify-between group hover:border-sky-500/30 transition-all">
          <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Wind Status</span>
            <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </div>

          <div class="my-3 flex items-center justify-between">
            <div>
              <div class="text-2xl font-extrabold text-white">
                {{ data.metrics.windSpeed }} <span class="text-xs font-normal text-slate-400">km/h</span>
              </div>
              <p class="text-xs text-slate-400 mt-1">
                Gusts to <strong class="text-slate-200">{{ data.metrics.windGusts }} km/h</strong>
              </p>
            </div>

            <!-- Compass Needle -->
            <div class="w-10 h-10 rounded-full bg-slate-800/80 border border-white/10 flex items-center justify-center relative">
              <svg
                class="w-6 h-6 text-sky-400 transition-transform duration-700"
                [style.transform]="'rotate(' + data.metrics.windDirectionDeg + 'deg)'"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19V5m0 0l-4 4m4-4l4 4" />
              </svg>
              <span class="absolute text-[8px] font-bold text-slate-300 top-0.5">{{ data.metrics.windDirectionCardinal }}</span>
            </div>
          </div>

          <div class="text-[11px] text-slate-400">
            Direction: <span class="text-slate-200 font-medium">{{ data.metrics.windDirectionCardinal }} ({{ data.metrics.windDirectionDeg }}°)</span>
          </div>
        </div>

        <!-- Humidity Card -->
        <div class="glass-card p-4 rounded-2xl flex flex-col justify-between group hover:border-blue-500/30 transition-all">
          <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Humidity</span>
            <svg class="w-4 h-4 text-blue-400 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>

          <div class="my-3">
            <div class="text-2xl font-extrabold text-white">
              {{ data.metrics.humidity }}<span class="text-xs font-normal text-slate-400">%</span>
            </div>
            <p class="text-xs text-slate-400 mt-1">
              Dew point is <strong class="text-slate-200">{{ data.metrics.dewPoint }}°C</strong>
            </p>
          </div>

          <div class="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div class="h-full bg-blue-400 rounded-full transition-all duration-500" [style.width.%]="data.metrics.humidity"></div>
          </div>
        </div>

        <!-- UV Index Card -->
        <div class="glass-card p-4 rounded-2xl flex flex-col justify-between group hover:border-amber-500/30 transition-all">
          <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>UV Index</span>
            <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>

          <div class="my-3">
            <div class="text-2xl font-extrabold text-white">
              {{ data.metrics.uvIndex }} <span class="text-xs font-normal text-slate-400">/ 12</span>
            </div>
            <p class="text-xs font-medium text-amber-300 mt-1">
              {{ data.metrics.uvLabel }} Risk
            </p>
          </div>

          <div class="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div
              class="h-full bg-amber-400 rounded-full transition-all duration-500"
              [style.width.%]="(data.metrics.uvIndex / 12) * 100"
            ></div>
          </div>
        </div>

        <!-- Sun Arc Card (Sunrise / Sunset) -->
        <div class="glass-card p-4 rounded-2xl flex flex-col justify-between group hover:border-orange-500/30 transition-all">
          <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Sunrise & Sunset</span>
            <svg class="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v2m0 14v2m9-9h-2M5 12H3" />
            </svg>
          </div>

          <div class="my-2 space-y-2">
            <div class="flex items-center justify-between text-xs">
              <span class="text-slate-400">🌅 Sunrise</span>
              <span class="font-bold text-white">{{ data.metrics.sunrise }}</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-slate-400">🌇 Sunset</span>
              <span class="font-bold text-white">{{ data.metrics.sunset }}</span>
            </div>
          </div>

          <div class="text-[10px] text-slate-400 text-center bg-slate-800/40 rounded-lg py-1">
            Daylight duration: ~13h 36m
          </div>
        </div>

        <!-- Pressure & Visibility Card -->
        <div class="glass-card p-4 rounded-2xl flex flex-col justify-between group hover:border-purple-500/30 transition-all">
          <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Pressure & Visibility</span>
            <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>

          <div class="my-2 space-y-1">
            <div class="text-xl font-extrabold text-white">
              {{ data.metrics.pressure }} <span class="text-xs font-normal text-slate-400">hPa</span>
            </div>
            <p class="text-xs text-slate-400">
              Visibility: <strong class="text-slate-200">{{ data.metrics.visibility }} km</strong>
            </p>
          </div>

          <div class="text-[10px] text-emerald-400 font-medium">
            Normal Atmospheric Pressure
          </div>
        </div>

      </div>
    }
  `
})
export class WeatherMetricsComponent {
  constructor(public weatherService: WeatherService) {}

  mathMin(a: number, b: number): number {
    return Math.min(a, b);
  }
}
