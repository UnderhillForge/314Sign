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

/**
 * GET /api/weather
 * Get weather data for a location using National Weather Service API (weather.gov)
 * Query params:
 *   - location: 'auto' (uses default) or
 *     - 'lat,lon' (e.g., '40.7128,-74.0060' for New York)
 *     - city name (will attempt to geocode)
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

    console.log(`Fetching weather for location: ${location}, units: ${units}`);
    
    // Fetch real weather data from NOAA/NWS
    const weatherData = await fetchWeatherDataFromNWS(location, units, location);
    
    // Cache the result
    cache.set(cacheKey, {
      data: weatherData,
      timestamp: Date.now()
    });

    console.log(`Successfully fetched weather for ${location}`);
    res.json({ success: true, data: weatherData });
  } catch (error) {
    console.error('Weather API error:', error instanceof Error ? error.message : error);
    // Return mock data on error as fallback
    const units = req.query.units as string || 'F';
    const mockData = getMockWeatherData('Your Location (Mock)', units);
    res.json({ 
      success: true, 
      data: mockData,
      mock: true,
      message: 'Using mock data - service unavailable',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Fetch weather data from National Weather Service (NOAA)
 * @param location - Location query (auto, coords, city name, or zip code)
 * @param units - Temperature units (F or C)
 * @param configuredLocation - Original configured location name to display
 */
async function fetchWeatherDataFromNWS(location: string, units: string, configuredLocation: string = location): Promise<any> {
  let lat: number, lon: number;

  // Parse location
  if (location === 'auto') {
    // Default location (New York City)
    lat = 40.7128;
    lon = -74.0060;
    console.log(`Using auto location: NYC (${lat}, ${lon})`);
  } else if (location.includes(',')) {
    // Try to parse as coordinates first (lat,lon format)
    const parts = location.split(',');
    if (parts.length === 2) {
      const latStr = parts[0].trim();
      const lonStr = parts[1].trim();
      const parsedLat = parseFloat(latStr);
      const parsedLon = parseFloat(lonStr);
      
      // If both parts parse as valid numbers, treat as coordinates
      if (!isNaN(parsedLat) && !isNaN(parsedLon)) {
        lat = parsedLat;
        lon = parsedLon;
        console.log(`Parsed as coordinates: (${lat}, ${lon})`);
      } else {
        // Otherwise, treat the whole string as a location name and geocode it
        console.log(`Not coordinates, geocoding as location: "${location}"`);
        const coords = await geocodeLocation(location);
        lat = coords.lat;
        lon = coords.lon;
        console.log(`Geocoded "${location}" to (${lat}, ${lon})`);
      }
    } else {
      // Geocode as location name
      console.log(`Geocoding location: "${location}"`);
      const coords = await geocodeLocation(location);
      lat = coords.lat;
      lon = coords.lon;
      console.log(`Geocoded "${location}" to (${lat}, ${lon})`);
    }
  } else {
    // Location name - use geocoding
    console.log(`Geocoding location: "${location}"`);
    const coords = await geocodeLocation(location);
    lat = coords.lat;
    lon = coords.lon;
    console.log(`Geocoded "${location}" to (${lat}, ${lon})`);
  }

  if (isNaN(lat) || isNaN(lon)) {
    throw new Error(`Failed to determine coordinates for location: ${location}. Got (${lat}, ${lon})`);
  }

  // Get the forecast URL from the points API
  const pointsData = await httpsGet(`https://api.weather.gov/points/${lat},${lon}`);
  
  if (pointsData.properties?.forecast && pointsData.properties?.forecastGridData) {
    // Get current conditions and forecast
    const forecastUrl = pointsData.properties.forecast;
    const forecastData = await httpsGet(forecastUrl);
    
    // Get grid point data for more detailed forecast
    const gridUrl = pointsData.properties.forecastGridData;
    const gridData = await httpsGet(gridUrl);

    // Use configured location name, fall back to NWS-derived location
    const displayLocation = configuredLocation && configuredLocation !== 'auto' 
      ? configuredLocation 
      : (pointsData.properties.relativeLocation?.properties?.city || 
         pointsData.properties.areaDescription ||
         `${lat.toFixed(2)}, ${lon.toFixed(2)}`);

    // Parse the forecast data
    return parseForecastData(forecastData, gridData, displayLocation, units);
  } else {
    throw new Error('Invalid location - outside NOAA service area');
  }
}

/**
 * Geocode a location name to coordinates
 * Supports: city names, city, state format, and US zip codes
 * Falls back to common US cities if geocoding fails
 */
async function geocodeLocation(locationName: string): Promise<{ lat: number; lon: number }> {
  const trimmed = locationName.toLowerCase().trim();
  
  // Check if it's a US zip code (5 digits or 5+4 format)
  if (/^\d{5}(-\d{4})?$/.test(trimmed)) {
    console.log(`Geocoding zip code: ${trimmed}`);
    try {
      // Use OpenStreetMap's nominatim to geocode zip code
      const response = await httpsGet(`https://nominatim.openstreetmap.org/search?postalcode=${encodeURIComponent(trimmed)}&countrycodes=us&format=json&limit=1`);
      if (Array.isArray(response) && response.length > 0) {
        const result = {
          lat: parseFloat(response[0].lat),
          lon: parseFloat(response[0].lon)
        };
        console.log(`Resolved zip code ${trimmed} to (${result.lat}, ${result.lon})`);
        return result;
      }
    } catch (e) {
      console.warn(`Failed to geocode zip code: ${trimmed}`);
    }
  }
  
  // Common US cities fallback
  const commonCities: Record<string, { lat: number; lon: number }> = {
    'new york': { lat: 40.7128, lon: -74.0060 },
    'los angeles': { lat: 34.0522, lon: -118.2437 },
    'chicago': { lat: 41.8781, lon: -87.6298 },
    'houston': { lat: 29.7604, lon: -95.3698 },
    'phoenix': { lat: 33.4484, lon: -112.0742 },
    'philadelphia': { lat: 39.9526, lon: -75.1652 },
    'san antonio': { lat: 29.4241, lon: -98.4936 },
    'san diego': { lat: 32.7157, lon: -117.1611 },
    'dallas': { lat: 32.7767, lon: -96.7970 },
    'san francisco': { lat: 37.7749, lon: -122.4194 },
    'seattle': { lat: 47.6062, lon: -122.3321 },
    'denver': { lat: 39.7392, lon: -104.9903 },
    'boston': { lat: 42.3601, lon: -71.0589 },
    'miami': { lat: 25.7617, lon: -80.1918 }
  };

  const normalized = locationName.toLowerCase().trim();
  if (commonCities[normalized]) {
    return commonCities[normalized];
  }

  // Try OpenCage Geocoder (free tier available)
  try {
    const response = await httpsGet(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(locationName)}&format=json&limit=1`);
    if (Array.isArray(response) && response.length > 0) {
      return {
        lat: parseFloat(response[0].lat),
        lon: parseFloat(response[0].lon)
      };
    }
  } catch (e) {
    // Fallback to NYC if geocoding fails
    console.warn(`Could not geocode "${locationName}", using default location`);
  }

  return { lat: 40.7128, lon: -74.0060 }; // Default to NYC
}

/**
 * Parse NWS forecast data into the format used by the slideshow
 */
function parseForecastData(forecastData: any, gridData: any, locationName: string, units: string): any {
  const properties = forecastData.properties;
  
  if (!properties || !properties.periods) {
    throw new Error('Invalid forecast data structure');
  }

  const periods = properties.periods;
  
  // Get current conditions (first period that's today/current)
  const currentPeriod = periods[0];
  const currentTemp = currentPeriod.temperature;
  const currentCondition = currentPeriod.shortForecast || currentPeriod.detailedForecast;
  
  // Convert temperature if needed
  let convertedTemp = currentTemp;
  if (units === 'C') {
    convertedTemp = Math.round((currentTemp - 32) * 5/9);
  }

  // Get wind speed from current period, handle different formats
  let windSpeed = 0;
  if (currentPeriod.windSpeed) {
    const windMatch = currentPeriod.windSpeed.match(/\d+/);
    windSpeed = windMatch ? parseInt(windMatch[0]) : 0;
  }

  // Convert wind speed if needed (NWS provides in mph)
  if (units === 'C') {
    windSpeed = Math.round(windSpeed * 1.60934); // mph to km/h
  }

  // Get humidity from relativeHumidity if available, else estimate
  let humidity = 65; // default
  if (gridData?.properties?.relativeHumidity?.values) {
    const humidityValues = gridData.properties.relativeHumidity.values;
    if (humidityValues.length > 0) {
      humidity = Math.round(humidityValues[0].value || 65);
    }
  }

  // Build forecast for next 3 days
  const forecast: Array<{ day: string; temp: number; condition: string; icon: string }> = [];
  const dayMap = new Map<string, any[]>();
  
  // Group periods by day
  periods.forEach((period: any) => {
    const date = new Date(period.startTime);
    const dayKey = date.toDateString();
    
    if (!dayMap.has(dayKey)) {
      dayMap.set(dayKey, []);
    }
    dayMap.get(dayKey)!.push(period);
  });

  // Get the next 3 days (starting from tomorrow)
  const days = Array.from(dayMap.entries()).slice(1, 4);
  
  days.forEach(([dayKey, dayPeriods]) => {
    // Get daytime period for forecast
    const daytimePeriod = dayPeriods.find((p: any) => !p.isDaytime || p.isDaytime === true) || dayPeriods[0];
    
    let temp = daytimePeriod.temperature;
    if (units === 'C') {
      temp = Math.round((temp - 32) * 5/9);
    }

    forecast.push({
      day: new Date(dayKey).toLocaleDateString('en-US', { weekday: 'short' }),
      temp: temp,
      condition: daytimePeriod.shortForecast || 'Unknown',
      icon: mapNWSIconToWeatherIcon(daytimePeriod.icon)
    });
  });

  return {
    location: locationName,
    current: {
      temp: convertedTemp,
      condition: currentCondition.split('.')[0], // Get just the main condition
      humidity: humidity,
      windSpeed: windSpeed,
      icon: mapNWSIconToWeatherIcon(currentPeriod.icon)
    },
    forecast: forecast,
    units: units,
    timestamp: Date.now(),
    source: 'NOAA National Weather Service'
  };
}

/**
 * Map NWS weather icons to OpenWeatherMap icon codes for compatibility
 * NWS icons are SVG URLs, we convert to OWM format for consistency
 */
function mapNWSIconToWeatherIcon(nwsIcon: string): string {
  if (!nwsIcon) return '02d'; // Default to cloudy

  const iconMap: Record<string, string> = {
    'skc': '01d',        // Clear/Sunny - day
    'few': '02d',        // Few clouds - day
    'sct': '03d',        // Scattered
    'bkn': '04d',        // Broken
    'ovc': '04d',        // Overcast
    'wind_skc': '01d',   // Clear and windy
    'wind_few': '02d',   // Few clouds and windy
    'wind_sct': '03d',   // Scattered and windy
    'wind_bkn': '04d',   // Broken and windy
    'wind_ovc': '04d',   // Overcast and windy
    'snow': '13d',       // Snow
    'rain_snow': '13d',  // Rain/snow
    'rain_sleet': '13d', // Rain/sleet
    'sleet': '13d',      // Sleet
    'rain': '09d',       // Rain
    'rain_fzra': '13d',  // Freezing rain
    'tsra': '11d',       // Thunderstorm
    'tornado': '11d',    // Tornado
    'fog': '50d',        // Fog
    'hail': '13d',       // Hail
    'mist': '50d',       // Mist
    'dust': '50d',       // Dust
    'smoke': '50d',      // Smoke
    'blizzard': '13d',   // Blizzard
  };

  // Check for night versions
  if (nwsIcon.includes('night')) {
    for (const [key, value] of Object.entries(iconMap)) {
      if (nwsIcon.includes(key)) {
        return value.replace('d', 'n'); // Convert day to night
      }
    }
    return '01n'; // Default to night/clear
  }

  // Check day versions
  for (const [key, value] of Object.entries(iconMap)) {
    if (nwsIcon.includes(key)) {
      return value;
    }
  }

  return '02d'; // Default to cloudy
}

/**
 * Helper function to make HTTPS GET requests
 */
function httpsGet(url: string): Promise<any> {
  console.log(`Making HTTPS request to: ${url}`);
  
  return new Promise((resolve, reject) => {
    https.get(url, { 
      headers: {
        'User-Agent': '314Sign-Weather/1.0 (Raspberry Pi Digital Signage)'
      }
    }, (res) => {
      let data = '';
      
      // Handle redirects
      if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        let redirectUrl = res.headers.location;
        
        // Convert relative URLs to absolute URLs 
        if (redirectUrl.startsWith('/')) {
          // Relative URL - extract host from original URL
          try {
            const urlObj = new URL(url);
            redirectUrl = `${urlObj.protocol}//${urlObj.host}${redirectUrl}`;
          } catch (e) {
            console.error('Failed to resolve relative redirect URL:', redirectUrl);
          }
        }
        
        console.log(`Redirect to: ${redirectUrl}`);
        httpsGet(redirectUrl).then(resolve).catch(reject);
        return;
      }
      
      if (res.statusCode && res.statusCode >= 400) {
        reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
        return;
      }
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          if (!data) {
            reject(new Error('Empty response from server'));
            return;
          }
          resolve(JSON.parse(data));
        } catch (error) {
          console.error('Failed to parse JSON from:', url);
          console.error('Response data:', data.substring(0, 500));
          reject(new Error('Failed to parse response'));
        }
      });
    }).on('error', (error) => {
      console.error(`HTTPS request error for ${url}:`, error.message);
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
