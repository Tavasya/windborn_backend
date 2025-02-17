from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import openmeteo_requests
import requests_cache
from retry_requests import retry
import httpx
import math
from datetime import datetime
from dotenv import load_dotenv
import os
from calcualtions import balloon_fall_coords
import requests
import base64
import uvicorn


load_dotenv()



app = FastAPI()




##  GET CURRENT TIME --> GET ALL WEATHER BALOONS COORDS OF THE CORRECT HOUR  ----> ----> POP BALOON ---> GET  SPECIFIC WEATHER BALLOON COORDS IN ONGITDUE AND LAIGTUDE




# --------------------------COORDS OF AIR BALLOON--------------------------------



# This represents hour 
hour = datetime.now().hour
API_URL = f"https://a.windbornesystems.com/treasure/{hour:02d}.json"


@app.get("/coords_all")
async def get_coords():
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL)
        if response.status_code == 200:
            try:
                # Replace any occurrence of NaN (not quoted) with null so that it becomes valid JSON.
                fixed_text = response.text.replace("NaN", "null")
                data = json.loads(fixed_text)
                return data
            except Exception as e:
                return {"error": f"Error decoding JSON: {e}"}
        else:
            return {"error": f"Failed to fetch data, status code: {response.status_code}"}







# --------------------------COVERTING ECEF TO GEODETIC--------------------------------
#Assuming the ballon coordinates are in ECEF, this function converts them to geodetic coordinates for the openmeteo API

def converter(x, y, z, tolerance=1e-12):
    """
    Convert ECEF coordinates to geodetic coordinates (latitude, longitude, altitude)
    using the WGS84 ellipsoid.

    Parameters:
        x, y, z : float
            ECEF coordinates in meters.
        tolerance : float
            Convergence tolerance for the iterative algorithm.

    Returns:
        lat_deg : float
            Latitude in degrees.
        lon_deg : float
            Longitude in degrees.
        alt : float
            Altitude above the ellipsoid in meters.
    """
    # WGS84 ellipsoid constants:
    a = 6378137.0                  # semi-major axis, meters
    b = 6356752.314245             # semi-minor axis, meters
    e2 = 1 - (b**2 / a**2)         # first eccentricity squared

    # Compute longitude (in radians)
    lon = math.atan2(y, x)

    # Compute p, the distance from the z-axis
    p = math.sqrt(x**2 + y**2)

    # Initial guess for latitude (in radians)
    lat = math.atan2(z, p * (1 - e2))
    lat_prev = 0

    # Iteratively improve the latitude value
    while abs(lat - lat_prev) > tolerance:
        lat_prev = lat
        N = a / math.sqrt(1 - e2 * math.sin(lat)**2)  # prime vertical radius of curvature
        lat = math.atan2(z + e2 * N * math.sin(lat), p)

    # Compute altitude
    N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
    alt = p / math.cos(lat) - N

    # Convert latitude and longitude from radians to degrees
    lat_deg = math.degrees(lat)
    lon_deg = math.degrees(lon)

    return lat_deg, lon_deg, alt


# Setup the Open-Meteo API client with caching and retry
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

@app.get("/weather")
async def get_weather(x: float, y: float, z: float):
    url = "https://api.open-meteo.com/v1/forecast"
    
    lat, lon, alt = converter(x, y, z)
    params = {
        "latitude": lat,
        "longitude": lon,
        "elevation": alt,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "surface_pressure",
            "wind_speed_10m",
            "wind_speed_80m",
            "wind_speed_120m",
            "wind_speed_180m",
            "wind_direction_10m",
            "wind_direction_80m",
            "wind_direction_120m",
            "wind_direction_180m",
            "wind_gusts_10m",
            "temperature_80m",
            "temperature_120m",
            "temperature_180m",
        ],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 1
    }

    # Get the weather data (assuming one location/model is returned)
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Build a dictionary from the response
    data = {
        "metadata": {
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
            "elevation": response.Elevation(),
            "timezone": response.Timezone(),
            "timezone_abbreviation": response.TimezoneAbbreviation(),
            "utc_offset_seconds": response.UtcOffsetSeconds()
        },
        "current": {
            "time": response.Current().Time(),
            "temperature_2m": response.Current().Variables(0).Value(),
            "relative_humidity_2m": response.Current().Variables(1).Value(),
            "surface_pressure": response.Current().Variables(2).Value(),
            "wind_speed_10m": response.Current().Variables(3).Value(),
            "wind_direction_10m": response.Current().Variables(4).Value(),
            "wind_gusts_10m": response.Current().Variables(5).Value(),
        },
        "hourly": {
            "time": response.Hourly().Time(),
            "interval": response.Hourly().Interval(),
            "temperature_2m": response.Hourly().Variables(0).ValuesAsNumpy().tolist(),
            "relative_humidity_2m": response.Hourly().Variables(1).ValuesAsNumpy().tolist(),
            "dew_point_2m": response.Hourly().Variables(2).ValuesAsNumpy().tolist(),
            "apparent_temperature": response.Hourly().Variables(3).ValuesAsNumpy().tolist(),
            "precipitation_probability": response.Hourly().Variables(4).ValuesAsNumpy().tolist(),
            "precipitation": response.Hourly().Variables(5).ValuesAsNumpy().tolist(),
            "weather_code": response.Hourly().Variables(6).ValuesAsNumpy().tolist(),
            "surface_pressure": response.Hourly().Variables(7).ValuesAsNumpy().tolist(),
            "wind_speed_10m": response.Hourly().Variables(8).ValuesAsNumpy().tolist(),
            "wind_speed_80m": response.Hourly().Variables(9).ValuesAsNumpy().tolist(),
            "wind_speed_120m": response.Hourly().Variables(10).ValuesAsNumpy().tolist(),
            "wind_speed_180m": response.Hourly().Variables(11).ValuesAsNumpy().tolist(),
            "wind_direction_10m": response.Hourly().Variables(12).ValuesAsNumpy().tolist(),
            "wind_direction_80m": response.Hourly().Variables(13).ValuesAsNumpy().tolist(),
            "wind_direction_120m": response.Hourly().Variables(14).ValuesAsNumpy().tolist(),
            "wind_direction_180m": response.Hourly().Variables(15).ValuesAsNumpy().tolist(),
            "wind_gusts_10m": response.Hourly().Variables(16).ValuesAsNumpy().tolist(),
            "temperature_80m": response.Hourly().Variables(17).ValuesAsNumpy().tolist(),
            "temperature_120m": response.Hourly().Variables(18).ValuesAsNumpy().tolist(),
            "temperature_180m": response.Hourly().Variables(19).ValuesAsNumpy().tolist(),
        }
    }

    return data






GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@app.get("/impact_location")
async def impact_location(x: float, y: float, z: float):
    lat, lon, alt = converter(x, y, z)
    lat_impact, lon_impact = balloon_fall_coords(lat, lon, alt)
    
    google_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat_impact},{lon_impact}&zoom=13&size=600x600&maptype=roadmap&markers=color:red%7Clabel:X%7C{lat_impact},{lon_impact}&key={GOOGLE_API_KEY}"
    
    response = requests.get(google_url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch map image")
    
    # Encode the image to base64
    image_base64 = base64.b64encode(response.content).decode('utf-8')
    
    # Prepare the response data
    response_data = {
        "latitude": lat_impact,
        "longitude": lon_impact,
        "image": image_base64
    }
    
    return JSONResponse(content=response_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

