"""
CarePath AI — OSRM Routing Service
Provides road distance, travel duration, and GeoJSON route geometry
between patient coordinates and specialist facilities via OSRM.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Tuple
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("services.routing")

# In-memory cache for OSRM routes within session: (p_lat, p_lon, s_lat, s_lon) -> route_dict
_ROUTE_CACHE: Dict[Tuple[float, float, float, float], Dict[str, Any]] = {}


class RoutingService:
    """Service for interacting with OSRM (Open Source Routing Machine) API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 3.5):
        # Allow override via settings or parameter, defaulting to demo server
        settings = get_settings()
        self.base_url = (base_url or getattr(settings, "osrm_base_url", "https://router.project-osrm.org")).rstrip("/")
        self.timeout = timeout

    async def get_route(
        self,
        patient_lat: float,
        patient_lon: float,
        specialist_lat: float,
        specialist_lon: float,
    ) -> Dict[str, Any]:
        """
        Fetch driving route from patient to specialist using OSRM.
        CRITICAL: OSRM expects coordinates in (longitude, latitude) order!
        """
        # Validate coordinates input
        if not self._is_valid_coordinate(patient_lat, patient_lon) or not self._is_valid_coordinate(specialist_lat, specialist_lon):
            logger.warning(
                "invalid_coordinates_for_routing",
                patient=(patient_lat, patient_lon),
                specialist=(specialist_lat, specialist_lon),
            )
            return {
                "available": False,
                "distance_meters": None,
                "distance_km": None,
                "duration_seconds": None,
                "duration_minutes": None,
                "geometry": None,
                "error": "Invalid coordinates provided",
            }

        # Round coordinates for cache key (~11m precision)
        cache_key = (
            round(patient_lat, 4),
            round(patient_lon, 4),
            round(specialist_lat, 4),
            round(specialist_lon, 4),
        )
        if cache_key in _ROUTE_CACHE:
            logger.debug("osrm_route_cache_hit", key=cache_key)
            return _ROUTE_CACHE[cache_key]

        # Construct OSRM request URL
        # OSRM format: /route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson
        url = f"{self.base_url}/route/v1/driving/{patient_lon},{patient_lat};{specialist_lon},{specialist_lat}"
        params = {
            "overview": "full",
            "geometries": "geojson",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                logger.warning(
                    "osrm_http_error",
                    status_code=response.status_code,
                    url=url,
                )
                return self._fallback_response(f"HTTP {response.status_code} from OSRM server")

            data = response.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                logger.warning("osrm_no_route_found", code=data.get("code"))
                return self._fallback_response(data.get("message", "No road route found"))

            route = data["routes"][0]
            dist_meters = float(route.get("distance", 0.0))
            dur_seconds = float(route.get("duration", 0.0))
            geometry = route.get("geometry")

            result = {
                "available": True,
                "distance_meters": round(dist_meters, 1),
                "distance_km": round(dist_meters / 1000.0, 2),
                "duration_seconds": round(dur_seconds, 1),
                "duration_minutes": round(dur_seconds / 60.0, 1),
                "geometry": geometry,
                "error": None,
            }

            # Cache successful route
            _ROUTE_CACHE[cache_key] = result
            logger.info(
                "osrm_route_success",
                distance_km=result["distance_km"],
                duration_minutes=result["duration_minutes"],
            )
            return result

        except httpx.TimeoutException:
            logger.warning("osrm_request_timeout", url=url)
            return self._fallback_response("OSRM server request timed out")
        except Exception as e:
            logger.error("osrm_routing_failed", error=str(e))
            return self._fallback_response(f"Routing error: {str(e)}")

    def _is_valid_coordinate(self, lat: float, lon: float) -> bool:
        """Verify latitude is [-90, 90] and longitude is [-180, 180]."""
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            return -90.0 <= lat_val <= 90.0 and -180.0 <= lon_val <= 180.0
        except (ValueError, TypeError):
            return False

    def _fallback_response(self, reason: str) -> Dict[str, Any]:
        """Return standardized fallback structure when OSRM is unavailable."""
        return {
            "available": False,
            "distance_meters": None,
            "distance_km": None,
            "duration_seconds": None,
            "duration_minutes": None,
            "geometry": None,
            "error": reason,
        }
