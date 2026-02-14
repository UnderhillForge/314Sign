import express, { Request, Response } from 'express';
import https from 'https';

const router = express.Router();

// Weather cache
interface WeatherCache {
  data: any;
  timestamp: number;
}

const cache: Map<string, WeatherCache> = new Map();
const CACHE_DURATION = 10 * 60 * 1000; // 10 minutes

// You can get a free API key from https://openweathermap.org/api
// Store it in environment variable OPENWEATHER_API_KEY
const API_KEY = process.env.OPENWEATHER_API_KEY || '';

/**
 * GET /api/weather
 * Get weather data for a location with caching
 * Query params:
 *   - location: 'auto' (uses IP geolocation) or city name
 *   - units: 'F' (Fahrenheit) or 'C' (Celsius)
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const location = req.query.location as string || 'auto';
    const units = req.query.units as string || 'F';
    
    // Check cache
    const cacheKey = `${location}-${units}`;
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return res.json({ success: true, data: cached.data, cached: true });
    }

    // If no API key, return mock data
    if (!API_KEY) {
      console.log('No OpenWeather API key found, returning mock data');
      const mockData = getMockWeatherData(location, units);
      return res.json({ success: true, data: mockData, mock: true });
    }

    // Fetch real weather data
    const weatherData = await fetchWeatherData(location, units);
    
    // Cache the result
    cache.set(cacheKey, {
      data: weatherData,
      timestamp: Date.now()
    });

    res.json({ success: true, data: weatherData });
  } catch (error) {
    console.error('Weather API error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch weather data',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Fetch weather data from OpenWeatherMap API
 */
async function fetchWeatherData(location: string, units: string): Promise<any> {
  const unitsParam = units === 'C' ? 'metric' : 'imperial';
  
  // Get coordinates for the location
  let lat: number, lon: number;
  
  if (location === 'auto') {
    // Use a default location if auto-detection isn't available
    // In production, you'd want to detect this from the client's IP
    lat = 40.7128;
    lon = -74.0060; // New York
  } else {
    // Geocode the location name
    const geoData = await httpsGet(`https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(location)}&limit=1&appid=${API_KEY}`);
    if (!geoData || geoData.length === 0) {
      throw new Error('Location not found');
    }
    lat = geoData[0].lat;
    lon = geoData[0].lon;
  }

  // Fetch current weather and forecast
  const [current, forecast] = await Promise.all([
    httpsGet(`https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=${unitsParam}&appid=${API_KEY}`),
    httpsGet(`https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&units=${unitsParam}&appid=${API_KEY}`)
  ]);

  // Parse forecast data to get daily forecasts
  const dailyForecasts = parseDailyForecasts(forecast.list, 3);

  return {
    location: current.name,
    current: {
      temp: Math.round(current.main.temp),
      condition: current.weather[0].main,
      description: current.weather[0].description,
      icon: current.weather[0].icon,
      humidity: current.main.humidity,
      windSpeed: Math.round(current.wind.speed)
    },
    forecast: dailyForecasts,
    units: units,
    timestamp: Date.now()
  };
}

/**
 * Parse 5-day forecast data into daily forecasts
 */
function parseDailyForecasts(forecastList: any[], days: number): any[] {
  const dailyData: Map<string, any[]> = new Map();
  
  // Group forecast entries by day
  forecastList.forEach(entry => {
    const date = new Date(entry.dt * 1000);
    const dayKey = date.toISOString().split('T')[0];
    
    if (!dailyData.has(dayKey)) {
      dailyData.set(dayKey, []);
    }
    dailyData.get(dayKey)!.push(entry);
  });

  // Get the next N days (skip today)
  const dates = Array.from(dailyData.keys()).slice(1, days + 1);
  
  return dates.map(dateKey => {
    const dayEntries = dailyData.get(dateKey)!;
    
    // Calculate average temp and most common condition
    const avgTemp = Math.round(
      dayEntries.reduce((sum, e) => sum + e.main.temp, 0) / dayEntries.length
    );
    
    const conditions = dayEntries.map(e => e.weather[0].main);
    const mostCommonCondition = conditions.sort((a, b) =>
      conditions.filter(c => c === a).length - conditions.filter(c => c === b).length
    ).pop();
    
    const icon = dayEntries.find(e => e.weather[0].main === mostCommonCondition)?.weather[0].icon || dayEntries[0].weather[0].icon;
    
    return {
      day: new Date(dateKey).toLocaleDateString('en-US', { weekday: 'short' }),
      temp: avgTemp,
      condition: mostCommonCondition,
      icon: icon
    };
  });
}

/**
 * Helper function to make HTTPS GET requests
 */
function httpsGet(url: string): Promise<any> {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(new Error('Failed to parse response'));
        }
      });
    }).on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Get mock weather data for testing
 */
function getMockWeatherData(location: string, units: string): any {
  return {
    location: location === 'auto' ? 'Your Location' : location,
    current: {
      temp: units === 'C' ? 22 : 72,
      condition: 'Partly Cloudy',
      description: 'partly cloudy',
      icon: '02d',
      humidity: 65,
      windSpeed: units === 'C' ? 15 : 10
    },
    forecast: [
      {
        day: 'Tomorrow',
        temp: units === 'C' ? 24 : 75,
        condition: 'Sunny',
        icon: '01d'
      },
      {
        day: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { weekday: 'short' }),
        temp: units === 'C' ? 20 : 68,
        condition: 'Rainy',
        icon: '10d'
      },
      {
        day: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { weekday: 'short' }),
        temp: units === 'C' ? 23 : 73,
        condition: 'Cloudy',
        icon: '03d'
      }
    ],
    units: units,
    timestamp: Date.now(),
    mock: true
  };
}

export default router;
