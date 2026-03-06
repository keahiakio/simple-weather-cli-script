import pytest
from unittest.mock import patch, MagicMock
from get_weather import geocode_location, get_weather_gov, display_weather_gov

def test_geocode_location_success():
    mock_response = {
        "results": [{
            "latitude": 45.0,
            "longitude": -93.0
        }]
    }
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        lat, lon = geocode_location("Minneapolis")
        assert lat == 45.0
        assert lon == -93.0

def test_geocode_location_not_found():
    mock_response = {"results": []}
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        result = geocode_location("NonExistentPlace")
        assert result is None

@patch('requests.get')
def test_get_weather_gov_flow(mock_get):
    # Mock points response
    mock_points = {
        "properties": {
            "forecast": "https://api.weather.gov/gridpoints/MPX/107,71/forecast",
            "forecastHourly": "https://api.weather.gov/gridpoints/MPX/107,71/forecast/hourly",
            "relativeLocation": {
                "properties": {"city": "Minneapolis", "state": "MN"}
            }
        }
    }
    # Mock daily forecast
    mock_daily = {
        "properties": {
            "generatedAt": "2026-03-03T12:00:00Z",
            "updated": "2026-03-03T11:00:00Z",
            "elevation": {"value": 250, "unitCode": "wmoUnit:m"},
            "periods": [
                {
                    "name": "Today",
                    "temperature": 32,
                    "temperatureUnit": "F",
                    "shortForecast": "Sunny",
                    "detailedForecast": "Mostly sunny today."
                }
            ]
        }
    }
    
    # Configure mock to return different responses based on URL
    def side_effect(url, headers=None, params=None):
        mock = MagicMock()
        mock.status_code = 200
        if "/points/" in url:
            mock.json.return_value = mock_points
        elif "/forecast/hourly" in url:
            mock.json.return_value = {"properties": {"periods": []}}
        else:
            mock.json.return_value = mock_daily
        return mock

    mock_get.side_effect = side_effect
    
    data = get_weather_gov(45.0, -93.0)
    assert data is not None
    assert data["daily"]["properties"]["periods"][0]["name"] == "Today"
    assert data["points"]["properties"]["relativeLocation"]["properties"]["city"] == "Minneapolis"

def test_display_weather_gov_no_data(capsys):
    display_weather_gov(None)
    captured = capsys.readouterr()
    assert "No valid weather data to display." in captured.err
