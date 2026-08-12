"""
Unit and Integration Tests for OSRM Routing Service and API Endpoint
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.routing_service import RoutingService


@pytest.mark.asyncio
async def test_routing_service_success():
    """Test successful OSRM route retrieval with geometry and metrics."""
    mock_osrm_response = {
        "code": "Ok",
        "routes": [
            {
                "distance": 14850.5,  # ~14.85 km
                "duration": 1110.2,   # ~18.5 min
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-118.2437, 34.0522],
                        [-118.2500, 34.0600],
                        [-118.3775, 34.0736],
                    ],
                },
            }
        ],
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_osrm_response
        mock_get.return_value = mock_response

        service = RoutingService()
        result = await service.get_route(
            patient_lat=34.0522,
            patient_lon=-118.2437,
            specialist_lat=34.0736,
            specialist_lon=-118.3775,
        )

        assert result["available"] is True
        assert result["distance_km"] == 14.85
        assert result["duration_minutes"] == 18.5
        assert result["geometry"]["type"] == "LineString"
        assert len(result["geometry"]["coordinates"]) == 3
        assert result["error"] is None

        # Verify OSRM argument order: lon,lat
        called_url = mock_get.call_args[0][0]
        assert "-118.2437,34.0522;-118.3775,34.0736" in called_url


@pytest.mark.asyncio
async def test_routing_service_invalid_coordinates():
    """Test handling of invalid lat/lon coordinates."""
    service = RoutingService()
    result = await service.get_route(
        patient_lat=999.0,  # Invalid lat
        patient_lon=-118.2437,
        specialist_lat=34.0736,
        specialist_lon=-118.3775,
    )

    assert result["available"] is False
    assert result["distance_km"] is None
    assert result["duration_minutes"] is None
    assert result["error"] == "Invalid coordinates provided"


@pytest.mark.asyncio
async def test_routing_service_http_failure_graceful_fallback():
    """Test graceful fallback when OSRM server returns non-200 or times out."""
    from app.services.routing_service import _ROUTE_CACHE
    _ROUTE_CACHE.clear()

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        service = RoutingService(timeout=0.1)
        result = await service.get_route(
            patient_lat=34.0522,
            patient_lon=-118.2437,
            specialist_lat=34.0736,
            specialist_lon=-118.3775,
        )

        assert result["available"] is False
        assert result["distance_km"] is None
        assert result["error"] == "OSRM server request timed out"


if __name__ == "__main__":
    asyncio.run(test_routing_service_success())
    asyncio.run(test_routing_service_invalid_coordinates())
    asyncio.run(test_routing_service_http_failure_graceful_fallback())
    print("ALL OSRM ROUTING TESTS PASSED SUCCESSFULLY!")
