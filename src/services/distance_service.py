import httpx
from fastapi import HTTPException, status
from src.core.config import ORS_API_KEY

ORS_GEOCODE_URL    = "https://api.openrouteservice.org/geocode/search"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def _geocode_city(city: str) -> tuple[float, float]:
    """
    Converts a city name to (longitude, latitude) using ORS Geocoding API.
    Raises 400 if city not found.
    """
    if not ORS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ORS_API_KEY not configured. Add it to your .env file.",
        )

    response = httpx.get(ORS_GEOCODE_URL, params={
        "api_key": ORS_API_KEY,
        "text":    city,
        "size":    1,
    }, timeout=10)

    data = response.json()

    if not data.get("features"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location not found: '{city}'. Try a more specific city name.",
        )

    coords = data["features"][0]["geometry"]["coordinates"]
    return float(coords[0]), float(coords[1])   # lon, lat


def get_road_distance_km(pickup_city: str, drop_city: str) -> float:
    """
    Returns the road distance in KM between two city names using ORS.
    Flow: city name → geocode → lat/lng → directions API → distance in km
    """
    pickup_lon, pickup_lat = _geocode_city(pickup_city)
    drop_lon,   drop_lat   = _geocode_city(drop_city)

    response = httpx.get(
        ORS_DIRECTIONS_URL,
        params={
            "api_key": ORS_API_KEY,
            "start":   f"{pickup_lon},{pickup_lat}",
            "end":     f"{drop_lon},{drop_lat}",
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not calculate distance. Check ORS API key or city names.",
        )

    data = response.json()
    distance_meters = data["features"][0]["properties"]["segments"][0]["distance"]
    return round(distance_meters / 1000, 2)   # convert meters → km
