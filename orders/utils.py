import osmnx as ox
import networkx as nx
from django.contrib.gis.db.models.functions import Distance
from routingpy import OSRM
from routingpy.exceptions import RouterApiError
from django.contrib.gis.geos import Point, LineString
from driver.models import Driver
from geopy.distance import geodesic
from datetime import timedelta, datetime
import heapq
import logging
import pickle
import os
from hashlib import md5

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CACHE_DIR = "graph_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def load_or_create_graph(center_lat, center_lon, dist):
    """
    Load OSM graph from cache or download and cache it.
    Uses rounded center and distance as a key.
    """
    key = f"{round(center_lat, 4)}_{round(center_lon, 4)}_{int(dist)}"
    filename = os.path.join(CACHE_DIR, md5(key.encode()).hexdigest() + ".pkl")

    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    G = ox.graph_from_point((center_lat, center_lon), dist=dist, network_type='drive')
    with open(filename, 'wb') as f:
        pickle.dump(G, f)

    return G


def get_osm_route(start_point, end_point, vehicle_speed_kmph=50):
    """
    Computes the shortest path using cached OSM graph and returns route info with steps.
    """
    try:
        start_lat, start_lon = start_point.y, start_point.x
        end_lat, end_lon = end_point.y, end_point.x

        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2
        dist = max(abs(start_lat - end_lat), abs(start_lon - end_lon)) * 111000 * 1.5
        dist = min(dist, 10000)

        G = load_or_create_graph(center_lat, center_lon, dist)

        start_node = ox.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.nearest_nodes(G, end_lon, end_lat)

        route = nx.shortest_path(G, start_node, end_node, weight='length', method='dijkstra')
        route_edges = list(zip(route[:-1], route[1:]))

        # Generate path and steps
        path_coords = []
        steps = []
        total_length = 0

        for u, v in route_edges:
            edge_data = G.get_edge_data(u, v, 0)  # take first if multiple edges
            geometry = edge_data.get("geometry")

            if geometry:
                coords = list(geometry.coords)
                for latlon in coords:
                    path_coords.append([latlon[0], latlon[1]])  # [lat, lon]
            else:
                u_data = G.nodes[u]
                v_data = G.nodes[v]
                path_coords.append([u_data['x'], u_data['y']])
                path_coords.append([v_data['x'], v_data['y']])
            # Add step info
            step_length = edge_data['length']
            total_length += step_length
            steps.append({
                'from': [G.nodes[u]['y'], G.nodes[u]['x']],
                'to': [G.nodes[v]['y'], G.nodes[v]['x']],
                'length_m': round(step_length, 1),
                'highway': edge_data.get('highway'),
                'name': edge_data.get('name', 'Unnamed road'),
            })

        distance_km = total_length / 1000.0
        estimated_time = timedelta(hours=distance_km / float(vehicle_speed_kmph))

        return {
            'total_distance_km': round(distance_km, 2),
            'estimated_time': estimated_time,
            'path_coords': path_coords,
            'steps': steps  # NEW: step-level detail
        }

    except Exception as e:
        logger.error(f"OSM routing error: {str(e)}")
        return None


def get_nearest_driver(delivery_point):
    """
    Finds the nearest available driver to a given point.
    """
    drivers = Driver.objects.filter(status='available').annotate(
        distance=Distance('location', delivery_point)
    ).order_by('distance')

    return drivers.first() if drivers.exists() else None


def get_traffic_multiplier():
    """
    Returns a traffic multiplier based on current time of day.
    """
    hour = datetime.now().hour
    return 2.0 if 7 <= hour <= 9 or 17 <= hour <= 19 else 1.0


def haversine_distance_km(point1, point2):
    """
    Calculates distance in kilometers between two GIS Points.
    """
    return geodesic((point1.y, point1.x), (point2.y, point2.x)).km



def calculate_time(distance_km, speed_kmph, traffic_multiplier=1.0):
    """
    Calculates ETA as timedelta.
    """
    hours = (distance_km / float(speed_kmph)) * traffic_multiplier
    return timedelta(hours=hours)


def fallback_route(start_point, end_point, vehicle_speed_kmph=40):
    """
    Fallback to straight-line distance calculation if OSRM fails.
    """
    traffic_multiplier = get_traffic_multiplier()
    distance_km = haversine_distance_km(start_point, end_point)
    estimated_time = calculate_time(distance_km, vehicle_speed_kmph, traffic_multiplier)
    
    # Create a simple straight line path
    path_coords = [
        [start_point.y, start_point.x],
        [end_point.y, end_point.x]
    ]
    
    return {
        'total_distance_km': round(distance_km, 2),
        'estimated_time': estimated_time,
        'path_coords': path_coords
    }


def generate_path_matrix(delivery_points, start_point, vehicle_speed_kmph=50):
    """
    Computes total route across multiple delivery points.
    
    Args:
        delivery_points (list of Point): Points to visit.
        start_point (Point): Starting location (usually driver's location).
        vehicle_speed_kmph (float): Speed in km/h.

    Returns:
        dict: {
            'total_distance_km': float,
            'estimated_time': timedelta,
            'path_coords': list of [lat, lon]
        }
    """
    if len(delivery_points) == 1:
        return get_osm_route(start_point, delivery_points[0], vehicle_speed_kmph)

    total_distance = 0
    total_time_seconds = 0
    all_path_coords = []

    current_point = start_point
    for i, next_point in enumerate(delivery_points):
        route = get_osm_route(current_point, next_point, vehicle_speed_kmph)

        if not route:
            logger.warning(f"Route failed between {current_point} and {next_point}")
            continue

        total_distance += route['total_distance_km']
        total_time_seconds += route['estimated_time'].total_seconds()

        if i == 0:
            all_path_coords.extend(route['path_coords'])
        else:
            all_path_coords.extend(route['path_coords'][1:])  # avoid duplicate point

        current_point = next_point

    return {
        'total_distance_km': round(total_distance, 2),
        'estimated_time': timedelta(seconds=total_time_seconds),
        'path_coords': all_path_coords
    }
