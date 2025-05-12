from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from driver.models import Driver
from geopy.distance import geodesic
from datetime import timedelta, datetime
import heapq


def get_nearest_driver(delivery_point):
    """
    Returns the nearest available driver based on current location.
    """
    drivers = Driver.objects.filter(status='available').annotate(
        distance=Distance('location', delivery_point)
    ).order_by('distance')

    return drivers.first() if drivers.exists() else None


def get_traffic_multiplier():
    """
    Returns a traffic multiplier based on the current time of day.
    """
    now = datetime.now().hour
    if 7 <= now <= 9 or 17 <= now <= 19:
        return 2.0  # Rush hour
    return 1.0  # Normal traffic


def haversine_distance_km(point1, point2):
    """
    Calculates distance in kilometers between two GIS Points.
    """
    return geodesic((point1.y, point1.x), (point2.y, point2.x)).km


def calculate_time(distance_km, speed_kmph, traffic_multiplier=1.0):
    """
    Calculates delivery time as timedelta.
    """
    hours = (float(distance_km) / float(speed_kmph)) * traffic_multiplier
    return timedelta(hours=hours)


def dijkstra_shortest_path(graph, start, end):
    """
    Simple Dijkstra algorithm implementation for shortest path.
    Graph format:
        {
            'A': {'B': distance_km, 'C': distance_km},
            'B': {'A': distance_km, 'C': distance_km, 'D': distance_km},
            ...
        }
    Returns: (total_distance, path_list)
    """
    queue = [(0, start, [])]
    visited = set()

    while queue:
        (dist, current, path) = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)
        path = path + [current]

        if current == end:
            return dist, path

        for neighbor, neighbor_dist in graph.get(current, {}).items():
            if neighbor not in visited:
                heapq.heappush(queue, (dist + neighbor_dist, neighbor, path))

    return float('inf'), []


def generate_path_matrix(delivery_points, start_point, vehicle_speed_kmph):
    """
    Generates an optimal path using Dijkstra and returns total time and path.
    `delivery_points` is a list of GIS Points (including end locations).
    `start_point` is the driver's location.
    """
    traffic_multiplier = get_traffic_multiplier()
    
    # Build a complete graph using haversine distances
    nodes = ['start'] + [f'd{i}' for i in range(len(delivery_points))]
    point_map = {'start': start_point}
    for i, pt in enumerate(delivery_points):
        point_map[f'd{i}'] = pt

    graph = {node: {} for node in nodes}
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if node1 == node2:
                continue
            dist = haversine_distance_km(point_map[node1], point_map[node2])
            graph[node1][node2] = dist

    # Dijkstra: from start to all delivery points in order
    total_distance = 0
    path = ['start']
    remaining = set(nodes) - {'start'}

    current = 'start'
    while remaining:
        next_node = min(remaining, key=lambda n: graph[current][n])
        total_distance += graph[current][next_node]
        path.append(next_node)
        remaining.remove(next_node)
        current = next_node

    estimated_time = calculate_time(total_distance, vehicle_speed_kmph, traffic_multiplier)
    final_path_coords = [point_map[node] for node in path]

    return {
        'total_distance_km': round(total_distance, 2),
        'estimated_time': estimated_time,
        'path_coords': [(pt.y, pt.x) for pt in final_path_coords]  # Latitude, Longitude
    }
