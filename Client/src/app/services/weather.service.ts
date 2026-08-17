import { Injectable, signal, computed, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { CompleteWeatherData, WeatherLocation } from '../models/weather.model';

@Injectable({
  providedIn: 'root'
})
export class WeatherService {
  readonly weatherData = signal<CompleteWeatherData | null>(null);
  readonly selectedLocation = signal<WeatherLocation>({
    name: 'London',
    country: 'United Kingdom',
    latitude: 51.5074,
    longitude: -0.1278
  });
  readonly viewingTarget = signal<{ date?: string; time?: string; label?: string; isHistorical?: boolean } | null>(null);
  readonly unit = signal<'C' | 'F'>('C');
  readonly theme = signal<'dark' | 'light'>('dark');
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly suggestions = signal<WeatherLocation[]>([]);

  // Computed helper for quick access
  readonly currentTemp = computed(() => {
    const data = this.weatherData();
    if (!data) return '--';
    return this.unit() === 'C'
      ? `${Math.round(data.current.tempC)}°C`
      : `${Math.round(data.current.tempF)}°F`;
  });

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    if (isPlatformBrowser(this.platformId)) {
      this.fetchWeatherForLocation(this.selectedLocation());
    } else {
      // On Node SSR server side, set initial mock data to prevent server-side SSL cert / network errors
      this.weatherData.set(this.generateMockWeatherData(this.selectedLocation()));
    }
  }

  toggleTheme(): void {
    const nextTheme = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(nextTheme);
    if (typeof document !== 'undefined') {
      if (nextTheme === 'light') {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
      } else {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
      }
    }
  }

  toggleUnit(): void {
    this.unit.set(this.unit() === 'C' ? 'F' : 'C');
  }

  async searchCities(query: string): Promise<WeatherLocation[]> {
    if (!query || query.trim().length < 2) {
      this.suggestions.set([]);
      return [];
    }

    try {
      const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
        query.trim()
      )}&count=6&language=en&format=json`;
      const res = await firstValueFrom(this.http.get<any>(url));
      if (res && res.results) {
        const locations: WeatherLocation[] = res.results.map((item: any) => ({
          name: item.name,
          country: item.country || '',
          admin1: item.admin1,
          latitude: item.latitude,
          longitude: item.longitude,
          timezone: item.timezone
        }));
        this.suggestions.set(locations);
        return locations;
      }
      this.suggestions.set([]);
      return [];
    } catch (err) {
      console.warn('Geocoding error, returning fallback suggestions:', err);
      this.suggestions.set([]);
      return [];
    }
  }

  async setLocation(location: WeatherLocation): Promise<void> {
    this.selectedLocation.set(location);
    this.suggestions.set([]);
    this.viewingTarget.set(null);
    await this.fetchWeatherForLocation(location);
  }

  async setLocationWithTarget(location: WeatherLocation, targetDate?: string, targetTime?: string, targetLabel?: string): Promise<void> {
    this.selectedLocation.set(location);
    this.suggestions.set([]);
    await this.fetchWeatherForLocation(location, targetDate, targetTime, targetLabel);
  }

  async resetToLive(): Promise<void> {
    this.viewingTarget.set(null);
    await this.fetchWeatherForLocation(this.selectedLocation());
  }

  async useCurrentLocation(): Promise<void> {
    this.isLoading.set(true);
    this.error.set(null);

    if (!navigator.geolocation) {
      this.error.set('Geolocation is not supported by your browser.');
      this.isLoading.set(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const location: WeatherLocation = {
          name: 'My Location',
          country: 'Current Position',
          latitude: lat,
          longitude: lon
        };
        await this.setLocation(location);
      },
      (err) => {
        console.warn('Geolocation error:', err);
        this.error.set('Could not get your precise location. Defaulting to London.');
        this.isLoading.set(false);
      }
    );
  }

  async fetchWeatherForLocation(
    loc: WeatherLocation,
    targetDate?: string,
    targetTime?: string,
    targetLabel?: string
  ): Promise<void> {
    this.isLoading.set(true);
    this.error.set(null);

    try {
      const todayIso = new Date().toISOString().split('T')[0];
      const isHistorical = !!(targetDate && targetDate < todayIso);

      let weatherUrl: string;

      if (isHistorical && targetDate) {
        // Calculate 7-day end date for historical query
        const tDate = new Date(targetDate);
        const endDateObj = new Date(tDate);
        endDateObj.setDate(endDateObj.getDate() + 6);
        const endIso = endDateObj.toISOString().split('T')[0];

        weatherUrl = `https://archive-api.open-meteo.com/v1/archive?latitude=${loc.latitude}&longitude=${loc.longitude}&start_date=${targetDate}&end_date=${endIso}&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m&timezone=auto`;
      } else {
        // Forecast query (covering past 2 days to next 16 days)
        weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${loc.latitude}&longitude=${loc.longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_probability_max,precipitation_sum,wind_speed_10m_max&forecast_days=16&past_days=2&timezone=auto`;
      }

      const airQualityUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${loc.latitude}&longitude=${loc.longitude}&current=us_aqi,pm10,pm2_5`;

      const [weatherRes, airRes] = await Promise.all([
        firstValueFrom(this.http.get<any>(weatherUrl)),
        firstValueFrom(this.http.get<any>(airQualityUrl)).catch(() => null)
      ]);

      const parsedData = this.parseOpenMeteoResponse(loc, weatherRes, airRes, targetDate, targetTime, targetLabel);
      this.weatherData.set(parsedData);
      if (targetDate || targetTime) {
        this.viewingTarget.set({
          date: targetDate,
          time: targetTime,
          label: targetLabel || targetDate,
          isHistorical
        });
      } else {
        this.viewingTarget.set(null);
      }
    } catch (err) {
      console.error('Failed to fetch weather from Open-Meteo, generating fallback:', err);
      this.weatherData.set(this.generateMockWeatherData(loc));
    } finally {
      this.isLoading.set(false);
    }
  }

  private parseOpenMeteoResponse(
    loc: WeatherLocation,
    weather: any,
    air: any,
    targetDate?: string,
    targetTime?: string,
    targetLabel?: string
  ): CompleteWeatherData {
    const current = weather.current || {};
    const hourly = weather.hourly || {};
    const daily = weather.daily || {};

    const dTimes: string[] = daily.time || [];
    const hTimes: string[] = hourly.time || [];

    // Find daily starting index (targetDate or today)
    let dailyStartIdx = 0;
    if (targetDate && dTimes.length > 0) {
      const idx = dTimes.indexOf(targetDate);
      if (idx !== -1) {
        dailyStartIdx = idx;
      }
    } else if (dTimes.length > 0) {
      const todayIso = new Date().toISOString().split('T')[0];
      const idx = dTimes.indexOf(todayIso);
      if (idx !== -1) {
        dailyStartIdx = idx;
      }
    }

    // Find hourly starting index (targetDate + targetTime or current hour)
    let hourlyStartIdx = 0;
    if (hTimes.length > 0) {
      if (targetDate) {
        const prefix = targetTime ? `${targetDate}T${targetTime.slice(0, 2)}` : `${targetDate}T`;
        const idx = hTimes.findIndex((t) => t.startsWith(prefix));
        if (idx !== -1) hourlyStartIdx = idx;
      } else if (targetTime) {
        const todayIso = new Date().toISOString().split('T')[0];
        const prefix = `${todayIso}T${targetTime.slice(0, 2)}`;
        const idx = hTimes.findIndex((t) => t.startsWith(prefix));
        if (idx !== -1) hourlyStartIdx = idx;
      } else {
        const nowPrefix = new Date().toISOString().slice(0, 13);
        const idx = hTimes.findIndex((t) => t.startsWith(nowPrefix));
        if (idx !== -1) hourlyStartIdx = idx;
      }
    }

    // Determine Hero Card Weather (If target is specified, use target's exact hour or day values)
    let tempC: number;
    let feelsLikeC: number;
    let code: number;
    let humidityVal: number;
    let windSpeed: number;
    let windDir: number;
    let isDayVal: boolean = true;
    let highC: number;
    let lowC: number;

    if (targetTime && hourly.temperature_2m && hourlyStartIdx < hourly.temperature_2m.length) {
      // Specific Hour
      tempC = hourly.temperature_2m[hourlyStartIdx] ?? 22;
      feelsLikeC = hourly.apparent_temperature ? hourly.apparent_temperature[hourlyStartIdx] : tempC;
      code = hourly.weather_code ? hourly.weather_code[hourlyStartIdx] : 0;
      humidityVal = hourly.relative_humidity_2m ? hourly.relative_humidity_2m[hourlyStartIdx] : 65;
      windSpeed = hourly.wind_speed_10m ? hourly.wind_speed_10m[hourlyStartIdx] : 12;
      windDir = hourly.wind_direction_10m ? hourly.wind_direction_10m[hourlyStartIdx] : 180;
      highC = daily.temperature_2m_max ? daily.temperature_2m_max[dailyStartIdx] : tempC + 3;
      lowC = daily.temperature_2m_min ? daily.temperature_2m_min[dailyStartIdx] : tempC - 3;
      const hrInt = parseInt(targetTime.slice(0, 2), 10);
      isDayVal = hrInt >= 6 && hrInt < 19;
    } else if (targetDate && daily.temperature_2m_max && dailyStartIdx < daily.temperature_2m_max.length) {
      // Specific Date
      highC = daily.temperature_2m_max[dailyStartIdx];
      lowC = daily.temperature_2m_min ? daily.temperature_2m_min[dailyStartIdx] : highC - 6;
      tempC = highC; // Display day's high / representative temp
      code = daily.weather_code ? daily.weather_code[dailyStartIdx] : 0;
      
      // Find noon hour for that day to get representative humidity & wind
      const noonIdx = hourlyStartIdx + 12 < (hourly.temperature_2m?.length || 0) ? hourlyStartIdx + 12 : hourlyStartIdx;
      feelsLikeC = hourly.apparent_temperature ? hourly.apparent_temperature[noonIdx] : tempC;
      humidityVal = hourly.relative_humidity_2m ? hourly.relative_humidity_2m[noonIdx] : 60;
      windSpeed = hourly.wind_speed_10m ? hourly.wind_speed_10m[noonIdx] : 12;
      windDir = hourly.wind_direction_10m ? hourly.wind_direction_10m[noonIdx] : 180;
      isDayVal = true;
    } else {
      // Live current weather
      tempC = current.temperature_2m ?? 22;
      feelsLikeC = current.apparent_temperature ?? tempC;
      code = current.weather_code ?? 0;
      humidityVal = current.relative_humidity_2m ?? 65;
      windSpeed = current.wind_speed_10m ?? 12;
      windDir = current.wind_direction_10m ?? 180;
      isDayVal = current.is_day === 1;
      highC = daily.temperature_2m_max ? daily.temperature_2m_max[dailyStartIdx] : tempC + 4;
      lowC = daily.temperature_2m_min ? daily.temperature_2m_min[dailyStartIdx] : tempC - 4;
    }

    const conditionInfo = this.getWeatherCodeInfo(code);
    const tempF = (tempC * 9) / 5 + 32;
    const feelsLikeF = (feelsLikeC * 9) / 5 + 32;

    const aqi = air?.current?.us_aqi ?? 35;
    const aqiLabel = this.getAqiLabel(aqi);
    const uv = daily.uv_index_max && daily.uv_index_max[dailyStartIdx] ? daily.uv_index_max[dailyStartIdx] : 4.5;

    // Hourly mapping: Slice 24 hours starting from hourlyStartIdx
    const hourlySlice = (hTimes || []).slice(hourlyStartIdx, hourlyStartIdx + 24);
    const hourlyList = hourlySlice.map((t: string, offset: number) => {
      const idx = hourlyStartIdx + offset;
      const hTempC = hourly.temperature_2m ? hourly.temperature_2m[idx] : tempC;
      const hCode = hourly.weather_code ? hourly.weather_code[idx] : code;
      const hInfo = this.getWeatherCodeInfo(hCode);
      const timeObj = new Date(t);
      const formattedTime = timeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      return {
        time: formattedTime,
        tempC: Math.round(hTempC),
        tempF: Math.round((hTempC * 9) / 5 + 32),
        condition: hInfo.label,
        icon: hInfo.icon,
        pop: hourly.precipitation_probability ? hourly.precipitation_probability[idx] : 10
      };
    });

    // Daily mapping: Slice 7 days starting from dailyStartIdx (shows next 7 days from target date!)
    const daysName = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dailySlice = (dTimes || []).slice(dailyStartIdx, dailyStartIdx + 7);
    const dailyList = dailySlice.map((d: string, offset: number) => {
      const idx = dailyStartIdx + offset;
      const dateObj = new Date(d);
      const todayIso = new Date().toISOString().split('T')[0];
      const dayName = d === todayIso ? 'Today' : daysName[dateObj.getDay()];
      const dCode = daily.weather_code ? daily.weather_code[idx] : 0;
      const dInfo = this.getWeatherCodeInfo(dCode);
      const maxC = daily.temperature_2m_max ? daily.temperature_2m_max[idx] : tempC + 2;
      const minC = daily.temperature_2m_min ? daily.temperature_2m_min[idx] : tempC - 4;

      return {
        day: dayName,
        date: `${dateObj.getMonth() + 1}/${dateObj.getDate()}`,
        tempMaxC: Math.round(maxC),
        tempMaxF: Math.round((maxC * 9) / 5 + 32),
        tempMinC: Math.round(minC),
        tempMinF: Math.round((minC * 9) / 5 + 32),
        condition: dInfo.label,
        icon: dInfo.icon,
        pop: daily.precipitation_probability_max ? daily.precipitation_probability_max[idx] : 20,
        uvIndex: daily.uv_index_max ? Math.round(daily.uv_index_max[idx]) : 5
      };
    });

    const formatSunTime = (isoString?: string) => {
      if (!isoString) return '06:30 AM';
      return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return {
      location: loc,
      current: {
        tempC: Math.round(tempC),
        tempF: Math.round(tempF),
        feelsLikeC: Math.round(feelsLikeC),
        feelsLikeF: Math.round(feelsLikeF),
        condition: conditionInfo.label,
        icon: conditionInfo.icon,
        highC: Math.round(highC),
        lowC: Math.round(lowC),
        highF: Math.round((highC * 9) / 5 + 32),
        lowF: Math.round((lowC * 9) / 5 + 32),
        humidity: Math.round(humidityVal),
        windSpeedKmH: Math.round(windSpeed),
        windDirection: windDir,
        windDirectionText: this.getCardinalDirection(windDir),
        pressureHpa: Math.round(current.surface_pressure ?? 1013),
        uvIndex: Number(uv.toFixed(1)),
        visibilityKm: 10,
        airQualityIndex: aqi,
        airQualityStatus: aqiLabel,
        sunrise: formatSunTime(daily.sunrise?.[dailyStartIdx] || daily.sunrise?.[0]),
        sunset: formatSunTime(daily.sunset?.[dailyStartIdx] || daily.sunset?.[0]),
        isDay: isDayVal
      },
      hourly: hourlyList,
      daily: dailyList,
      metrics: {
        airQualityIndex: aqi,
        airQualityLabel: aqiLabel,
        windSpeed: Math.round(windSpeed),
        windGusts: Math.round(windSpeed * 1.3),
        windDirectionDeg: windDir,
        windDirectionCardinal: this.getCardinalDirection(windDir),
        humidity: Math.round(humidityVal),
        dewPoint: Math.round(tempC - (100 - humidityVal) / 5),
        uvIndex: Number(uv.toFixed(1)),
        uvLabel: this.getUvLabel(uv),
        sunrise: formatSunTime(daily.sunrise?.[dailyStartIdx] || daily.sunrise?.[0]),
        sunset: formatSunTime(daily.sunset?.[dailyStartIdx] || daily.sunset?.[0]),
        pressure: Math.round(current.surface_pressure ?? 1013),
        visibility: 10
      },
      lastUpdated: new Date()
    };
  }

  private getWeatherCodeInfo(code: number): { label: string; icon: string } {
    if (code === 0) return { label: 'Clear Sky', icon: 'sun' };
    if (code >= 1 && code <= 3) return { label: 'Partly Cloudy', icon: 'cloud-sun' };
    if (code === 45 || code === 48) return { label: 'Foggy', icon: 'cloud-fog' };
    if (code >= 51 && code <= 67) return { label: 'Light Rain', icon: 'cloud-rain' };
    if (code >= 71 && code <= 77) return { label: 'Snowfall', icon: 'snowflake' };
    if (code >= 80 && code <= 82) return { label: 'Rain Showers', icon: 'cloud-drizzle' };
    if (code >= 95) return { label: 'Thunderstorm', icon: 'cloud-lightning' };
    return { label: 'Overcast', icon: 'cloud' };
  }

  private getCardinalDirection(deg: number): string {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return directions[Math.round(deg / 45) % 8];
  }

  private getAqiLabel(aqi: number): string {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    return 'Unhealthy';
  }

  private getUvLabel(uv: number): string {
    if (uv <= 2) return 'Low';
    if (uv <= 5) return 'Moderate';
    if (uv <= 7) return 'High';
    if (uv <= 10) return 'Very High';
    return 'Extreme';
  }

  private generateMockWeatherData(loc: WeatherLocation): CompleteWeatherData {
    return {
      location: loc,
      current: {
        tempC: 24,
        tempF: 75,
        feelsLikeC: 25,
        feelsLikeF: 77,
        condition: 'Partly Cloudy',
        icon: 'cloud-sun',
        highC: 28,
        lowC: 18,
        highF: 82,
        lowF: 64,
        humidity: 58,
        windSpeedKmH: 14,
        windDirection: 210,
        windDirectionText: 'SW',
        pressureHpa: 1015,
        uvIndex: 5.2,
        visibilityKm: 10,
        airQualityIndex: 38,
        airQualityStatus: 'Good',
        sunrise: '06:12 AM',
        sunset: '07:48 PM',
        isDay: true
      },
      hourly: [
        { time: '12:00 PM', tempC: 24, tempF: 75, condition: 'Sun', icon: 'sun', pop: 0 },
        { time: '01:00 PM', tempC: 26, tempF: 79, condition: 'Sun', icon: 'sun', pop: 0 },
        { time: '02:00 PM', tempC: 28, tempF: 82, condition: 'Partly Cloudy', icon: 'cloud-sun', pop: 10 },
        { time: '03:00 PM', tempC: 27, tempF: 80, condition: 'Partly Cloudy', icon: 'cloud-sun', pop: 15 },
        { time: '04:00 PM', tempC: 26, tempF: 79, condition: 'Light Rain', icon: 'cloud-rain', pop: 40 },
        { time: '05:00 PM', tempC: 24, tempF: 75, condition: 'Cloudy', icon: 'cloud', pop: 20 }
      ],
      daily: [
        { day: 'Today', date: '08/13', tempMaxC: 28, tempMaxF: 82, tempMinC: 18, tempMinF: 64, condition: 'Partly Cloudy', icon: 'cloud-sun', pop: 15, uvIndex: 5 },
        { day: 'Fri', date: '08/14', tempMaxC: 29, tempMaxF: 84, tempMinC: 19, tempMinF: 66, condition: 'Sunny', icon: 'sun', pop: 0, uvIndex: 7 },
        { day: 'Sat', date: '08/15', tempMaxC: 26, tempMaxF: 79, tempMinC: 17, tempMinF: 62, condition: 'Rain Showers', icon: 'cloud-rain', pop: 60, uvIndex: 4 },
        { day: 'Sun', date: '08/16', tempMaxC: 25, tempMaxF: 77, tempMinC: 16, tempMinF: 60, condition: 'Thunderstorm', icon: 'cloud-lightning', pop: 85, uvIndex: 3 },
        { day: 'Mon', date: '08/17', tempMaxC: 27, tempMaxF: 80, tempMinC: 18, tempMinF: 64, condition: 'Clear Sky', icon: 'sun', pop: 5, uvIndex: 6 },
        { day: 'Tue', date: '08/18', tempMaxC: 28, tempMaxF: 82, tempMinC: 19, tempMinF: 66, condition: 'Partly Cloudy', icon: 'cloud-sun', pop: 10, uvIndex: 6 },
        { day: 'Wed', date: '08/19', tempMaxC: 30, tempMaxF: 86, tempMinC: 20, tempMinF: 68, condition: 'Hot & Sunny', icon: 'sun', pop: 0, uvIndex: 8 }
      ],
      metrics: {
        airQualityIndex: 38,
        airQualityLabel: 'Good',
        windSpeed: 14,
        windGusts: 18,
        windDirectionDeg: 210,
        windDirectionCardinal: 'SW',
        humidity: 58,
        dewPoint: 15,
        uvIndex: 5.2,
        uvLabel: 'Moderate',
        sunrise: '06:12 AM',
        sunset: '07:48 PM',
        pressure: 1015,
        visibility: 10
      },
      lastUpdated: new Date()
    };
  }
}
