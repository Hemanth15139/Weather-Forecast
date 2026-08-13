import { Component, signal, ElementRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WeatherService } from '../../services/weather.service';
import { WeatherLocation } from '../../models/weather.model';

@Component({
  selector: 'app-weather-card',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="glass-panel rounded-3xl p-6 md:p-8 relative overflow-hidden transition-all duration-300">
      <!-- Ambient Glow Behind Weather Icon -->
      <div class="absolute -top-12 -right-12 w-64 h-64 bg-sky-500/20 rounded-full blur-3xl pointer-events-none animate-pulse-glow"></div>
      
      <!-- Top Bar: Search & Location -->
      <div class="relative z-20 flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        
        <!-- Search Container -->
        <div class="relative flex-1 max-w-md">
          <div class="relative flex items-center">
            <svg class="w-5 h-5 text-slate-400 absolute left-3.5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              [(ngModel)]="searchQuery"
              (input)="onSearchInput()"
              placeholder="Search location (e.g. London, Tokyo)..."
              class="w-full glass-input rounded-2xl pl-11 pr-10 py-2.5 text-sm focus:outline-none transition-all duration-200"
            />
            @if (searchQuery) {
              <button (click)="clearSearch()" class="absolute right-3 text-slate-400 hover:text-white text-sm">
                ✕
              </button>
            }
          </div>

          <!-- Suggestions Dropdown -->
          @if (weatherService.suggestions().length > 0) {
            <div class="absolute top-full left-0 right-0 mt-2 glass-panel bg-slate-900/90 rounded-2xl border border-white/10 shadow-2xl overflow-hidden z-50">
              @for (loc of weatherService.suggestions(); track loc.latitude + '' + loc.longitude) {
                <button
                  (click)="selectLocation(loc)"
                  class="w-full text-left px-4 py-3 hover:bg-white/10 flex items-center justify-between text-sm transition-colors border-b border-white/5 last:border-none"
                >
                  <span class="font-medium text-slate-200">{{ loc.name }}</span>
                  <span class="text-xs text-slate-400">{{ loc.admin1 ? loc.admin1 + ', ' : '' }}{{ loc.country }}</span>
                </button>
              }
            </div>
          }
        </div>

        <!-- Action Buttons: Geolocation & Unit Switch -->
        <div class="flex items-center gap-3 self-end md:self-auto">
          <button
            (click)="useLocation()"
            title="Use current GPS location"
            class="glass-card px-3.5 py-2.5 rounded-2xl flex items-center gap-2 text-xs font-semibold text-slate-200 hover:text-white transition-all active:scale-95"
          >
            <svg class="w-4 h-4 text-sky-400 animate-spin-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="hidden sm:inline">My Location</span>
          </button>

          <!-- °C / °F Unit Toggle -->
          <div class="glass-card p-1 rounded-2xl flex items-center">
            <button
              (click)="weatherService.unit.set('C')"
              [class.bg-sky-500]="weatherService.unit() === 'C'"
              [class.text-white]="weatherService.unit() === 'C'"
              [class.text-slate-400]="weatherService.unit() !== 'C'"
              class="px-3 py-1 rounded-xl text-xs font-bold transition-all"
            >
              °C
            </button>
            <button
              (click)="weatherService.unit.set('F')"
              [class.bg-sky-500]="weatherService.unit() === 'F'"
              [class.text-white]="weatherService.unit() === 'F'"
              [class.text-slate-400]="weatherService.unit() !== 'F'"
              class="px-3 py-1 rounded-xl text-xs font-bold transition-all"
            >
              °F
            </button>
          </div>
        </div>

      </div>

      <!-- Quick City Chips -->
      <div class="flex flex-wrap items-center gap-2 mb-6 text-xs">
        <span class="text-slate-400 font-medium mr-1">Popular:</span>
        @for (city of popularCities; track city.name) {
          <button
            (click)="selectLocation(city)"
            class="px-3 py-1 rounded-full glass-card hover:border-sky-400/50 text-slate-300 hover:text-white transition-all"
          >
            {{ city.name }}
          </button>
        }
      </div>

      <!-- Loading State -->
      @if (weatherService.isLoading()) {
        <div class="py-16 flex flex-col items-center justify-center text-center">
          <div class="w-12 h-12 border-4 border-sky-400 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p class="text-slate-300 text-sm animate-pulse">Fetching real-time satellite weather data...</p>
        </div>
      } @else if (weatherService.weatherData(); as data) {
        
        <!-- Main Weather Display -->
        <div class="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          
          <!-- Left: Location Info & Temp -->
          <div class="md:col-span-7 space-y-2">
            <div class="flex items-center gap-2">
              <h1 class="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
                {{ data.location.name }}
              </h1>
              <span class="text-xs px-2.5 py-1 rounded-full bg-white/10 text-sky-300 font-semibold border border-sky-400/20">
                {{ data.location.country || 'Live' }}
              </span>
            </div>
            
            <p class="text-xs text-slate-400 flex items-center gap-2">
              <span>Updated {{ data.lastUpdated | date:'shortTime' }}</span>
              <span>•</span>
              <span class="text-emerald-400 font-medium">Live Satellite Sync</span>
            </p>

            <div class="pt-4 flex items-baseline gap-4">
              <span class="text-6xl md:text-7xl font-black text-white tracking-tight drop-shadow-md">
                {{ weatherService.unit() === 'C' ? data.current.tempC : data.current.tempF }}°
              </span>
              <div class="space-y-1">
                <div class="text-lg font-bold text-sky-200">
                  {{ data.current.condition }}
                </div>
                <div class="text-xs text-slate-300 flex items-center gap-3">
                  <span>H: <strong class="text-white">{{ weatherService.unit() === 'C' ? data.current.highC : data.current.highF }}°</strong></span>
                  <span>L: <strong class="text-white">{{ weatherService.unit() === 'C' ? data.current.lowC : data.current.lowF }}°</strong></span>
                </div>
              </div>
            </div>

            <p class="text-xs text-slate-300 pt-2">
              Feels like <strong class="text-white font-semibold">{{ weatherService.unit() === 'C' ? data.current.feelsLikeC : data.current.feelsLikeF }}°</strong>
              with {{ data.current.humidity }}% humidity & {{ data.current.windSpeedKmH }} km/h wind.
            </p>
          </div>

          <!-- Right: Animated Weather Visual Icon -->
          <div class="md:col-span-5 flex flex-col items-center justify-center py-4">
            <div class="relative w-36 h-36 md:w-44 md:h-44 flex items-center justify-center animate-float">
              <!-- Render Weather SVG Icon based on condition -->
              <ng-container [ngSwitch]="data.current.icon">
                
                <!-- Sun / Clear -->
                <svg *ngSwitchCase="'sun'" class="w-full h-full text-amber-400 drop-shadow-[0_0_25px_rgba(251,191,36,0.5)]" fill="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="5" class="animate-pulse" />
                  <path stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" class="animate-spin-slow origin-center" />
                </svg>

                <!-- Rain / Drizzle -->
                <svg *ngSwitchCase="'cloud-rain'" class="w-full h-full text-sky-400 drop-shadow-[0_0_25px_rgba(56,189,248,0.5)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                  <path stroke-linecap="round" stroke-width="2" d="M8 19v3m4-3v3m4-3v3" class="animate-bounce" />
                </svg>

                <!-- Thunderstorm -->
                <svg *ngSwitchCase="'cloud-lightning'" class="w-full h-full text-indigo-400 drop-shadow-[0_0_25px_rgba(129,140,248,0.6)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 11l-3 5h4l-2 5" class="text-amber-400 animate-pulse" />
                </svg>

                <!-- Default Cloud Sun -->
                <svg *ngSwitchDefault class="w-full h-full text-sky-300 drop-shadow-[0_0_20px_rgba(56,189,248,0.4)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                  <circle cx="17" cy="8" r="3" class="fill-amber-400 stroke-amber-400 animate-pulse" />
                </svg>

              </ng-container>
            </div>
            
            <div class="mt-2 text-center">
              <span class="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800/80 text-sky-300 border border-sky-500/20">
                {{ data.current.condition }}
              </span>
            </div>
          </div>

        </div>
      }
    </div>
  `
})
export class WeatherCardComponent {
  searchQuery = '';

  popularCities: WeatherLocation[] = [
    { name: 'London', country: 'United Kingdom', latitude: 51.5074, longitude: -0.1278 },
    { name: 'New York', country: 'United States', latitude: 40.7128, longitude: -74.006 },
    { name: 'Tokyo', country: 'Japan', latitude: 35.6762, longitude: 139.6503 },
    { name: 'Paris', country: 'France', latitude: 48.8566, longitude: 2.3522 },
    { name: 'Sydney', country: 'Australia', latitude: -33.8688, longitude: 151.2093 },
    { name: 'Mumbai', country: 'India', latitude: 19.076, longitude: 72.8777 }
  ];

  constructor(
    public weatherService: WeatherService,
    private elementRef: ElementRef
  ) {}

  onSearchInput(): void {
    if (this.searchQuery.trim().length >= 2) {
      this.weatherService.searchCities(this.searchQuery);
    }
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.weatherService.suggestions.set([]);
  }

  selectLocation(loc: WeatherLocation): void {
    this.searchQuery = '';
    this.weatherService.setLocation(loc);
  }

  useLocation(): void {
    this.weatherService.useCurrentLocation();
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.weatherService.suggestions.set([]);
    }
  }
}
