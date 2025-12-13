"""Geo utilities for 2GIS integration and distance formatting."""

import math


def get_2gis_link(latitude: float, longitude: float) -> str:
    """Generate 2GIS link for coordinates.

    Returns URL that opens 2GIS app or web with the specified location.
    Format: https://2gis.kg/bishkek/geo/{lon},{lat}

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        2GIS URL string
    """
    # 2GIS uses lon,lat order
    return f"https://2gis.kg/bishkek/geo/{longitude},{latitude}"


def get_2gis_deeplink(latitude: float, longitude: float) -> str:
    """Generate 2GIS deeplink for mobile apps.

    Format: dgis://2gis.kg/routeSearch/rsType/car/to/{lon},{lat}
    """
    return f"dgis://2gis.kg/geo/{longitude},{latitude}"


def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate distance between two points using Haversine formula.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def format_distance(meters: float, lang: str = "ru") -> str:
    """Format distance for display.

    Args:
        meters: Distance in meters
        lang: Language code ("ru" or "kg")

    Returns:
        Formatted string like "500м" or "2.3км"
    """
    if meters < 1000:
        return f"{int(meters)}м"
    else:
        km = meters / 1000
        if km < 10:
            return f"{km:.1f}км"
        else:
            return f"{int(km)}км"
