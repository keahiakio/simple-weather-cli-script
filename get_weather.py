#!/usr/bin/env python3
import requests
import sys
import re
from datetime import datetime

GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"

def geocode_location(query):
    """
    Geocodes a location query using Open-Meteo Geocoding API.
    Returns (latitude, longitude) or None if not found.
    """
    params = {
        "name": query,
        "count": 1
    }
    try:
        response = requests.get(GEOCODING_BASE_URL, params=params)
        response.raise_for_status()
        results = response.json()
        if results and "results" in results and len(results["results"]) > 0:
            location = results["results"][0]
            return location["latitude"], location["longitude"]
        else:
            print(f"Could not find coordinates for '{query}'.", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error during geocoding '{query}': {e}", file=sys.stderr)
        return None

def geocode_zipcode(zipcode):
    """
    Geocodes a zipcode using Open-Meteo Geocoding API.
    Returns (latitude, longitude) or None if not found.
    """
    # The Open-Meteo API can handle zip codes directly as a "name" query.
    return geocode_location(zipcode)


def get_weather_gov(latitude, longitude):
    """
    Fetches weather forecast from weather.gov API for a given lat/lon.
    """
    points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    headers = {
        "User-Agent": "GeminiCLI WeatherApp/1.0 (keahiakio@example.com)"
    }
    
    try:
        # Step 1: Get the forecast URLs from the points endpoint
        points_response = requests.get(points_url, headers=headers)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        forecast_url = points_data.get("properties", {}).get("forecast")
        forecast_hourly_url = points_data.get("properties", {}).get("forecastHourly")
        
        if not forecast_url:
            print("Could not retrieve forecast URL from weather.gov API.", file=sys.stderr)
            return None
            
        # Step 2: Get the forecasts
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status()
        daily_data = forecast_response.json()

        hourly_data = None
        if forecast_hourly_url:
            hourly_response = requests.get(forecast_hourly_url, headers=headers)
            if hourly_response.status_code == 200:
                hourly_data = hourly_response.json()

        return {
            "daily": daily_data,
            "hourly": hourly_data,
            "points": points_data
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data from weather.gov: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return None

def display_weather_gov(data_dict):
    """
    Displays weather information from the weather.gov forecast data,
    including the current forecast and an hourly forecast.
    """
    if not data_dict or 'daily' not in data_dict:
        print("No valid weather data to display.", file=sys.stderr)
        return

    daily_data = data_dict['daily']
    hourly_data = data_dict.get('hourly')
    
    if not daily_data or "properties" not in daily_data or "periods" not in daily_data['properties']:
        print("No valid daily forecast data.", file=sys.stderr)
        return

    print(f"Weather forecast from weather.gov")
    if 'generatedAt' in daily_data['properties']:
        print(f"Generated at: {daily_data['properties']['generatedAt']}")
    if 'updated' in daily_data['properties']:
        print(f"Updated: {daily_data['properties']['updated']}")
    
    points_data = data_dict.get('points', {})
    if 'properties' in points_data and 'relativeLocation' in points_data['properties']:
        city = points_data['properties']['relativeLocation']['properties'].get('city')
        state = points_data['properties']['relativeLocation']['properties'].get('state')
        if city and state:
            print(f"Location: {city}, {state}")

    if 'elevation' in daily_data['properties'] and 'value' in daily_data['properties']['elevation']:
        elevation_val = daily_data['properties']['elevation']['value']
        elevation_unit = daily_data['properties']['elevation']['unitCode'].split(':')[-1]
        print(f"Elevation: {elevation_val} {elevation_unit}")
    print("-" * 20)

    daily_periods = daily_data['properties']['periods']
    
    # Display up to the first 3 daily periods
    print("Daily Summary:")
    for i, period in enumerate(daily_periods):
        if i >= 3:
            break
        temp_type = "Low" if "Night" in period['name'] or "Tonight" in period['name'] else "High"
        
        print(f"{period['name']}:")
        print(f"  Temperature {temp_type}: {period['temperature']}°{period['temperatureUnit']}")
        if 'shortForecast' in period:
            print(f"  Forecast: {period['shortForecast']}")
        if 'detailedForecast' in period:
            print(f"  Detailed: {period['detailedForecast']}")
        print("")

    if hourly_data and "properties" in hourly_data and "periods" in hourly_data['properties']:
        print("-" * 20)
        print("Hourly Forecast (Next 48 Hours):")
        hourly_periods = hourly_data['properties']['periods']
        
        current_day = None
        # Display next 48 hours, showing every other hour
        for i, period in enumerate(hourly_periods[:48:2]):
            # 2026-02-20T09:00:00-05:00
            start_time_str = period['startTime']
            try:
                # Basic ISO format parsing (handling offset)
                dt = datetime.fromisoformat(start_time_str)
                day_str = dt.strftime("%A, %b %d")
                time_str = dt.strftime("%I:%M %p")
            except ValueError:
                day_str = "Unknown Day"
                time_str = start_time_str

            if day_str != current_day:
                current_day = day_str
                print(f"\n{day_str}:")
            
            print(f"  {time_str}: {period['temperature']}°{period['temperatureUnit']} - {period['shortForecast']}")
        print("")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./get_weather.py <latitude> <longitude>", file=sys.stderr)
        print("       ./get_weather.py <city or airport name>", file=sys.stderr)
        print("       ./get_weather.py <zipcode>", file=sys.stderr)
        sys.exit(1)

    lat = None
    lon = None

    if len(sys.argv) == 3: # Assuming lat/lon input
        try:
            lat = float(sys.argv[1])
            lon = float(sys.argv[2])
        except ValueError:
            print("If providing two arguments, they must be valid latitude and longitude numbers.", file=sys.stderr)
            sys.exit(1)
    elif len(sys.argv) == 2: # Assuming city/airport name or zipcode
        input_query = sys.argv[1]
        if re.fullmatch(r"^\d{5}(-\d{4})?$", input_query): # Basic check for US zip code format
            print(f"Attempting to geocode zipcode: {input_query}")
            coords = geocode_zipcode(input_query)
            if coords:
                lat, lon = coords
        else:
            print(f"Attempting to geocode location: {input_query}")
            coords = geocode_location(input_query)
            if coords:
                lat, lon = coords
    else:
        print("Invalid number of arguments.", file=sys.stderr)
        print("Usage: ./get_weather.py <latitude> <longitude>", file=sys.stderr)
        print("       ./get_weather.py <city or airport name>", file=sys.stderr)
        print("       ./get_weather.py <zipcode>", file=sys.stderr)
        sys.exit(1)

    if lat is None or lon is None:
        print("Could not determine coordinates for the given input.", file=sys.stderr)
        sys.exit(1)

    weather_data = get_weather_gov(lat, lon)
    if weather_data:
        display_weather_gov(weather_data)

