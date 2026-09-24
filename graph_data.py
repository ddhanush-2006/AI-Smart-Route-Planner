# =============================================================================
#  graph_data.py — City Graph Construction
#  Defines all locations (nodes) and roads (edges) for the navigation system.
#  Each edge carries: distance (km), traffic level (1-3), travel_time (min)
# =============================================================================

import networkx as nx


def create_city_graph():
    """
    Builds and returns the city navigation graph.

    Node attributes:
        pos : (x, y) tuple used for A* heuristic and matplotlib visualization

    Edge attributes:
        distance    : Road length in kilometres
        traffic     : Congestion level — 1=Low, 2=Medium, 3=High
        travel_time : Estimated travel time in minutes (varies with traffic)

    Returns:
        G         : networkx.Graph object
        locations : dict  {location_name: (x, y)}
    """

    G = nx.Graph()  # Undirected graph — roads go both ways

    # ─── 14 City Locations with (x, y) layout coordinates ────────────────────
    # Coordinates are used both for drawing and for A* Euclidean heuristic.
    # They represent a conceptual map layout, NOT real GPS coordinates.
    locations = {
        "Airport":      (1, 9),
        "Park":         (3, 9),
        "Hospital":     (5, 8),
        "Stadium":      (7, 9),
        "Museum":       (9, 8),
        "Old Town":     (1, 6),
        "Central Hub":  (4, 6),
        "Mall":         (7, 6),
        "Harbor":       (9, 5),
        "University":   (2, 4),
        "Station":      (5, 4),
        "Tech Park":    (8, 3),
        "Suburb":       (3, 2),
        "Suburb West":  (6, 1),
    }

    # Register every location as a graph node, storing its position
    for name, pos in locations.items():
        G.add_node(name, pos=pos)

    # ─── Road Network (Edges) ─────────────────────────────────────────────────
    # Format: (from_node, to_node, distance_km, traffic_1-3, travel_time_min)
    #
    # traffic key:
    #   1 = Low    → roads are clear, fast travel
    #   2 = Medium → moderate congestion, slight delay
    #   3 = High   → heavy traffic, significant delay
    #
    # travel_time is pre-computed from distance + traffic effect:
    #   base_time = (distance / 40 km/h) * 60 min
    #   multiplier: 1.0x (low) | 1.5x (medium) | 2.5x (high)
    edges = [
        # ── North Ring ────────────────────────────────────────────────────────
        ("Airport",     "Park",         4,  1,  6),
        ("Park",        "Hospital",     4,  2,  9),
        ("Hospital",    "Stadium",      4,  3, 15),
        ("Stadium",     "Museum",       4,  2,  9),

        # ── Airport & Old Town connections ────────────────────────────────────
        ("Airport",     "Old Town",     5,  2, 11),
        ("Park",        "Central Hub",  4,  1,  6),
        ("Hospital",    "Central Hub",  4,  2,  9),
        ("Museum",      "Harbor",       3,  1,  5),

        # ── Middle Belt ───────────────────────────────────────────────────────
        ("Old Town",    "University",   4,  1,  6),
        ("Old Town",    "Central Hub",  5,  2, 11),
        ("Central Hub", "Mall",         5,  2, 11),
        ("Central Hub", "Station",      3,  1,  5),
        ("Central Hub", "University",   3,  2,  7),
        ("Mall",        "Stadium",      4,  3, 15),
        ("Mall",        "Harbor",       4,  2,  9),
        ("Mall",        "Tech Park",    4,  3, 15),
        ("Harbor",      "Tech Park",    3,  1,  5),

        # ── South Ring ────────────────────────────────────────────────────────
        ("University",  "Station",      3,  2,  7),
        ("University",  "Suburb",       4,  1,  6),
        ("Station",     "Tech Park",    5,  2, 11),
        ("Station",     "Suburb",       4,  1,  6),
        ("Station",     "Suburb West",  5,  3, 19),
        ("Tech Park",   "Suburb West",  4,  2,  9),
        ("Suburb",      "Suburb West",  4,  1,  6),
    ]

    for u, v, dist, traffic, time in edges:
        G.add_edge(u, v, distance=dist, traffic=traffic, travel_time=time)

    return G, locations
