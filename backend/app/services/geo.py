import math
import re

from app.models.road import Road


def wkt_centroid(wkt: str | None) -> tuple[float | None, float | None]:
    if not wkt:
        return None, None

    coords = re.findall(r"([\d.+-]+)\s+([\d.+-]+)", wkt)
    if not coords:
        return None, None

    lngs = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return radius * 2 * math.asin(math.sqrt(a))


def find_nearby_roads(
    roads: list[Road],
    lat: float,
    lng: float,
    radius_km: float,
) -> list[tuple[Road, float]]:
    nearby: list[tuple[Road, float]] = []

    for road in roads:
        road_lat, road_lng = wkt_centroid(road.geometry)
        if road_lat is None or road_lng is None:
            continue
        distance = haversine_km(lat, lng, road_lat, road_lng)
        if distance <= radius_km:
            nearby.append((road, distance))

    nearby.sort(key=lambda item: item[1])
    return nearby
