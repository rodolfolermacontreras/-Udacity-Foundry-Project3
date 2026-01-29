# app/tools/weather.py
"""
Weather Tool using Open-Meteo API
Provides weather forecasts for travel planning.
"""

from semantic_kernel.functions import kernel_function
import requests
import logging

logger = logging.getLogger(__name__)


class WeatherTools:
    """Weather tools for the Travel Concierge Agent."""
    
    @kernel_function(name="get_weather", description="Get weather forecast from Open-Meteo API for given coordinates")
    def get_weather(self, lat: float, lon: float) -> dict:
        """
        Get weather forecast for given coordinates using Open-Meteo API.
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            
        Returns:
            Dictionary with weather forecast data including:
            - latitude, longitude, timezone
            - daily: time, temperature_2m_max, temperature_2m_min, weathercode
        """
        try:
            # Open-Meteo API endpoint
            url = "https://api.open-meteo.com/v1/forecast"
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "forecast_days": 7,
                "timezone": "UTC"
            }
            
            logger.info(f"🌤️ Fetching weather for coordinates ({lat}, {lon})")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"✅ Weather data retrieved successfully")
            
            return {
                "latitude": data.get("latitude", lat),
                "longitude": data.get("longitude", lon),
                "timezone": data.get("timezone", "UTC"),
                "daily": data.get("daily", {}),
                "daily_units": data.get("daily_units", {})
            }
            
        except requests.exceptions.Timeout:
            logger.error("❌ Weather API timeout")
            raise Exception("Weather API timeout - please try again")
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Weather API HTTP error: {e}")
            raise Exception(f"Weather API error: {e}")
        except Exception as e:
            logger.error(f"❌ Weather API error: {e}")
            raise Exception(f"Failed to get weather data: {e}")
    
    @kernel_function(name="get_weather_for_city", description="Get weather forecast for a city by name")
    def get_weather_for_city(self, city: str) -> dict:
        """
        Get weather forecast for a city by name.
        First geocodes the city, then fetches weather data.
        
        Args:
            city: Name of the city
            
        Returns:
            Dictionary with weather forecast data
        """
        try:
            # Geocode the city using Open-Meteo geocoding API
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocode_params = {"name": city, "count": 1}
            
            logger.info(f"📍 Geocoding city: {city}")
            
            geocode_response = requests.get(geocode_url, params=geocode_params, timeout=10)
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()
            
            if not geocode_data.get("results"):
                raise Exception(f"City '{city}' not found")
            
            result = geocode_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            
            logger.info(f"✅ Found {city} at ({lat}, {lon})")
            
            # Get weather for the coordinates
            weather_data = self.get_weather(lat, lon)
            
            # Add city info to the result
            weather_data["city"] = result.get("name", city)
            weather_data["country"] = result.get("country", "Unknown")
            
            return weather_data
            
        except Exception as e:
            logger.error(f"❌ Error getting weather for city {city}: {e}")
            raise