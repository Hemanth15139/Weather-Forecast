import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WeatherService } from '../../services/weather.service';

@Component({
  selector: 'app-forecast-timeline',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (weatherService.weatherData(); as data) {
      <div class="space-y-6">
        
        <!-- Hourly Forecast Section -->
        <div class="glass-panel p-5 rounded-3xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Hourly Forecast
            </h3>
            <span class="text-xs text-slate-400">Next 24 Hours</span>
          </div>

          <!-- Horizontal Scroll Container -->
          <div class="flex items-center gap-3 overflow-x-auto pb-3 pt-1 scrollbar-thin">
            @for (item of data.hourly; track item.time + item.tempC) {
              <div class="glass-card p-3 rounded-2xl flex flex-col items-center min-w-[76px] hover:border-sky-400/50 transition-all shrink-0">
                <span class="text-xs text-slate-400 font-medium mb-2">{{ item.time }}</span>
                
                <div class="w-8 h-8 my-1 flex items-center justify-center text-sky-300">
                  <ng-container [ngSwitch]="item.icon">
                    <svg *ngSwitchCase="'sun'" class="w-6 h-6 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="5" />
                    </svg>
                    <svg *ngSwitchCase="'cloud-rain'" class="w-6 h-6 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                    </svg>
                    <svg *ngSwitchDefault class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                    </svg>
                  </ng-container>
                </div>

                <span class="text-sm font-extrabold text-white my-1">
                  {{ weatherService.unit() === 'C' ? item.tempC : item.tempF }}°
                </span>

                <!-- Rain % pill if > 10% -->
                @if (item.pop > 10) {
                  <span class="text-[10px] font-bold text-sky-400 flex items-center gap-0.5">
                    💧 {{ item.pop }}%
                  </span>
                } @else {
                  <span class="text-[10px] text-slate-500">0%</span>
                }
              </div>
            }
          </div>
        </div>

        <!-- 7-Day Extended Forecast Section -->
        <div class="glass-panel p-5 rounded-3xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              7-Day Extended Forecast
            </h3>
            <span class="text-xs text-slate-400">Weekly Outlook</span>
          </div>

          <div class="space-y-2.5">
            @for (day of data.daily; track day.day + day.date) {
              <div class="glass-card px-4 py-3 rounded-2xl flex items-center justify-between gap-4 hover:border-white/20 transition-all">
                
                <!-- Day & Date -->
                <div class="w-24 shrink-0">
                  <div class="text-sm font-bold text-white">{{ day.day }}</div>
                  <div class="text-[11px] text-slate-400">{{ day.date }}</div>
                </div>

                <!-- Condition Icon & Label -->
                <div class="flex items-center gap-2.5 flex-1 min-w-0">
                  <div class="w-6 h-6 text-sky-400 shrink-0">
                    <ng-container [ngSwitch]="day.icon">
                      <svg *ngSwitchCase="'sun'" class="w-6 h-6 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="5" />
                      </svg>
                      <svg *ngSwitchCase="'cloud-rain'" class="w-6 h-6 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                      </svg>
                      <svg *ngSwitchDefault class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                      </svg>
                    </ng-container>
                  </div>
                  <span class="text-xs text-slate-300 truncate hidden sm:inline">{{ day.condition }}</span>
                </div>

                <!-- Precipitation % -->
                <div class="w-14 text-center shrink-0">
                  @if (day.pop > 15) {
                    <span class="text-xs font-bold text-sky-400">💧 {{ day.pop }}%</span>
                  } @else {
                    <span class="text-xs text-slate-500">Dry</span>
                  }
                </div>

                <!-- Temperature Range Bar -->
                <div class="flex items-center gap-3 w-36 sm:w-44 shrink-0">
                  <span class="text-xs text-slate-400 w-7 text-right">
                    {{ weatherService.unit() === 'C' ? day.tempMinC : day.tempMinF }}°
                  </span>
                  
                  <div class="flex-1 bg-slate-800/80 rounded-full h-2 overflow-hidden relative">
                    <div class="h-full bg-gradient-to-r from-sky-400 via-amber-300 to-rose-400 rounded-full"></div>
                  </div>

                  <span class="text-xs font-extrabold text-white w-7">
                    {{ weatherService.unit() === 'C' ? day.tempMaxC : day.tempMaxF }}°
                  </span>
                </div>

              </div>
            }
          </div>
        </div>

      </div>
    }
  `
})
export class ForecastTimelineComponent {
  constructor(public weatherService: WeatherService) {}
}
