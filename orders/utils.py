import osmnx as ox
import networkx as nx
from driver.models import Driver
from django.contrib.gis.db.models.functions import Distance
from geopy.distance import geodesic
from datetime import timedelta, datetime
import heapq
from routingpy import OSRM
from routingpy.exceptions import RouterApiError
import logging

def get_osm_route(start_point, end_point):
    """Get route using Dijkstra's algorithm on real OpenStreetMap data"""
    try:
        # Convert points to lat/lon format
        start_lat, start_lon = start_point.y, start_point.x
        end_lat, end_lon = end_point.y, end_point.x
        
        # Get the street network around the points
        # Buffer distance in meters to ensure we capture enough of the network
        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2
        dist = max(abs(start_lat - end_lat), abs(start_lon - end_lon)) * 111000 * 1.5  # Convert to meters with buffer
        
        # Download and create the graph from OSM data
        G = ox.graph_from_point((center_lat, center_lon), dist=dist, network_type='drive')
        
        # Get nearest nodes to start and end points
        start_node = ox.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.nearest_nodes(G, end_lon, end_lat)
        
        # Calculate shortest path using Dijkstra's algorithm
        route = nx.shortest_path(G, start_node, end_node, weight='length', method='dijkstra')
        
        # Get the route coordinates
        path_coords = []
        for node in route:
            # Get node coordinates and convert to [lon, lat] format
            lon, lat = G.nodes[node]['x'], G.nodes[node]['y']
            path_coords.append([lon, lat])
        
        # Calculate total distance in meters
        distance_m = sum(ox.utils_graph.get_route_edge_attributes(G, route, 'length'))
        distance_km = distance_m / 1000
        
        # Estimate time based on distance and average speed (50 km/h)
        hours = distance_km / 50  # Assuming average speed of 50 km/h
        estimated_time = timedelta(hours=hours)
        
        return {
            'total_distance_km': round(distance_km, 2),
            'estimated_time': estimated_time,
            'path_coords': path_coords
        }
        
    except Exception as e:
        logger.error(f"OSM routing error: {str(e)}")
        # Fall back to haversine distance if OSM routing fails
        return fallback_route(start_point, end_point)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OSRM client - using the public API
# You can change this to your own OSRM server if you have one
osrm_client = OSRM()


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


def get_osrm_route(start_point, end_point):
    print(f"OSRM route requested from {start_point} to {end_point}")
    """
    Get the actual road-based route between two points using OSRM.
    
    Args:
        start_point: GIS Point object (driver location)
        end_point: GIS Point object (delivery location)
        
    Returns:
        dict with total_distance_km, estimated_time, and path_coords
    """
    try:
        # OSRM expects coordinates as [longitude, latitude]
        start_coords = [start_point.x, start_point.y]
        end_coords = [end_point.x, end_point.y]
        
        # Call OSRM API to get the route
        route = osrm_client.directions(
            locations=[start_coords, end_coords],
            profile='driving',
            overview='full',
            alternatives=False,
            steps=True,
            continue_straight=True,
            annotations=True
        )
        
        # Extract the route information
        # The Direction object doesn't have status_code attribute
        # Instead, check if geometry exists and has coordinates
        if route.geometry and len(route.geometry) > 0:
            # Get the geometry (path coordinates)
            path_coords = []
            for coord in route.geometry:
                # OSRM returns [longitude, latitude], but we store as [latitude, longitude]
                path_coords.append([coord[1], coord[0]])
            
            # Get the distance in kilometers
            distance_km = route.distance / 1000.0  # Convert meters to kilometers
            
            # Get the duration in seconds and convert to timedelta
            duration_seconds = route.duration
            estimated_time = timedelta(seconds=duration_seconds)
            
            print(f"OSRM route found with {len(path_coords)} points")
            
            return {
                'total_distance_km': round(distance_km, 2),
                'estimated_time': estimated_time,
                'path_coords': path_coords
            }
        else:
            logger.error("OSRM API returned no geometry")
            # Fall back to haversine distance if OSRM fails
            return fallback_route(start_point, end_point)
            
    except RouterApiError as e:
        logger.error(f"OSRM API error: {str(e)}")
        # Fall back to haversine distance if OSRM fails
        return fallback_route(start_point, end_point)
    except Exception as e:
        logger.error(f"Unexpected error in get_osrm_route: {str(e)}")
        # Fall back to haversine distance if anything goes wrong
        return fallback_route(start_point, end_point)


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


def generate_path_matrix(delivery_points, start_point, vehicle_speed_kmph):
    """
    Generates an optimal path using OpenStreetMap routing and returns total time and path.
    `delivery_points` is a list of GIS Points (including end locations).
    `start_point` is the driver's location.
    
    If there are multiple delivery points, we'll use a simple approach:
    1. Get the route from start_point to the first delivery point
    2. For each subsequent delivery point, get the route from the previous point
    """
    # If we only have one delivery point, just get the direct route
    if len(delivery_points) == 1:
        return get_osrm_route(start_point, delivery_points[0])
    
    # For multiple delivery points, calculate routes between each consecutive point
    total_distance = 0
    total_time_seconds = 0
    all_path_coords = []
    
    # First route: from start to first delivery point
    current_point = start_point
    for i, next_point in enumerate(delivery_points):
        # Get route from current point to next point
        route_segment = get_osrm_route(current_point, next_point)
        
        # Add distance and time
        total_distance += route_segment['total_distance_km']
        total_time_seconds += route_segment['estimated_time'].total_seconds()
        
        # Add path coordinates (skip the first point if not the first segment to avoid duplicates)
        if i == 0:
            all_path_coords.extend(route_segment['path_coords'])
        else:
            all_path_coords.extend(route_segment['path_coords'][1:])  # Skip the first point to avoid duplicates
        
        # Update current point for next iteration
        current_point = next_point
    
    return {
        'total_distance_km': round(total_distance, 2),
        'estimated_time': timedelta(seconds=total_time_seconds),
        'path_coords': all_path_coords
    }
