import osmnx as ox
import networkx as nx
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, LineString
from driver.models import Driver
from geopy.distance import geodesic
from datetime import timedelta, datetime
import heapq
import logging
import pickle
import os
from hashlib import md5
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import requests

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


def remove_consecutive_duplicates(path):
    cleaned_path = []
    prev = None
    for point in path:
        if point != prev:
            cleaned_path.append(point)
            prev = point
    return cleaned_path


def generate_path_matrix(delivery_points, start_point, vehicle_speed_kmph=50):
    """
    Computes optimized route visiting all delivery points from start_point using Dijkstra.
    """

    # Step 1: Build graph from center of all points
    all_lats = [pt.y for pt in delivery_points] + [start_point.y]
    all_lons = [pt.x for pt in delivery_points] + [start_point.x]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    dist = max([geodesic((lat, lon), (center_lat, center_lon)).meters for lat, lon in zip(all_lats, all_lons)]) * 2
    dist = min(dist, 10000)

    G = load_or_create_graph(center_lat, center_lon, dist)

    # Step 2: Get OSM nodes
    points = [start_point] + delivery_points
    nodes = [ox.nearest_nodes(G, pt.x, pt.y) for pt in points]

    # Step 3: Use greedy nearest-neighbor (or better: solve TSP for optimal order)
    path_coords = []
    visited = set()
    total_distance = 0
    total_time = 0

    current_node = nodes[0]
    visited.add(current_node)

    remaining_nodes = set(nodes[1:])
    while remaining_nodes:
        # Find nearest unvisited node
        next_node = min(remaining_nodes, key=lambda n: nx.shortest_path_length(G, current_node, n, weight='length'))
        path = nx.shortest_path(G, current_node, next_node, weight='length')
        edges = list(zip(path[:-1], path[1:]))

        for u, v in edges:
            data = G.get_edge_data(u, v, 0)
            length = data['length']
            total_distance += length

            geometry = data.get("geometry")
            if geometry:
                coords = list(geometry.coords)
            else:
                coords = [
                    (G.nodes[u]['x'], G.nodes[u]['y']),
                    (G.nodes[v]['x'], G.nodes[v]['y'])
                ]

            for lon, lat in coords:
                path_coords.append([lon, lat])

        cleaned_coords = remove_consecutive_duplicates(path_coords)

        total_time += (length / 1000.0) / float(vehicle_speed_kmph) * 3600
        current_node = next_node
        visited.add(next_node)
        remaining_nodes.remove(next_node)

    return {
        'total_distance_km': round(total_distance / 1000.0, 2),
        'estimated_time': timedelta(seconds=int(total_time)),
        'path_coords': cleaned_coords
    }


def send_fcm_notification(fcm_token, title, body, data=None):
    """
    Send FCM notification to a specific device
    """
    if not fcm_token:
        return None

    headers = {
        'Authorization': f'key={settings.FCM_SERVER_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'to': fcm_token,
        'notification': {
            'title': title,
            'body': body,
            'sound': 'default'
        },
        'data': data or {}
    }

    try:
        response = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error sending FCM notification: {str(e)}")
        return None


def send_order_notification(order, notification_type, users, title, body, data=None):
    """
    Send notifications to users about an order
    """
    notifications = []
    for user in users:
        # Create notification in database
        notification = Notification.objects.create(
            user=user,
            order=order,
            type=notification_type,
            title=title,
            body=body
        )
        notifications.append(notification)

        # Send FCM notification if user has FCM token
        if hasattr(user, 'fcm_token') and user.fcm_token:
            send_fcm_notification(
                fcm_token=user.fcm_token,
                title=title,
                body=body,
                data=data
            )

    return notifications