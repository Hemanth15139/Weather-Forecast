export interface WeatherLocation {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  timezone?: string;
  admin1?: string;
}

export interface CurrentWeather {
  tempC: number;
  tempF: number;
  feelsLikeC: number;
  feelsLikeF: number;
  condition: string;
  icon: string;
  highC: number;
  lowC: number;
  highF: number;
  lowF: number;
  humidity: number;
  windSpeedKmH: number;
  windDirection: number;
  windDirectionText: string;
  pressureHpa: number;
  uvIndex: number;
  visibilityKm: number;
  airQualityIndex: number;
  airQualityStatus: string;
  sunrise: string;
  sunset: string;
  isDay: boolean;
}

export interface HourlyForecast {
  time: string;
  tempC: number;
  tempF: number;
  condition: string;
  icon: string;
  pop: number; // probability of precipitation %
}

export interface DailyForecast {
  day: string;
  date: string;
  tempMaxC: number;
  tempMaxF: number;
  tempMinC: number;
  tempMinF: number;
  condition: string;
  icon: string;
  pop: number;
  uvIndex: number;
}

export interface WeatherMetrics {
  airQualityIndex: number;
  airQualityLabel: string;
  windSpeed: number;
  windGusts: number;
  windDirectionDeg: number;
  windDirectionCardinal: string;
  humidity: number;
  dewPoint: number;
  uvIndex: number;
  uvLabel: string;
  sunrise: string;
  sunset: string;
  pressure: number;
  visibility: number;
}

export interface CompleteWeatherData {
  location: WeatherLocation;
  current: CurrentWeather;
  hourly: HourlyForecast[];
  daily: DailyForecast[];
  metrics: WeatherMetrics;
  lastUpdated: Date;
}
