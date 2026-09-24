# =============================================================================
#  utils.py — Shared Helper Utilities
#
#  Provides reusable helper functions consumed by gui.py:
#    • Location sorting and binary-search lookup
#    • Path statistics computation (distance, time, traffic)
#    • Human-readable formatting helpers
#    • Preference → weight key mapping
# =============================================================================

from algorithms import binary_search_location


# ─────────────────────────────────────────────────────────────────────────────
#  LOCATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_sorted_locations(graph):
    """
    Returns an alphabetically sorted list of all node names in the graph.
    The sorted order is required by binary_search_location().

    Parameters:
        graph : networkx.Graph

    Returns:
        list[str] — sorted location names
    """
    return sorted(graph.nodes())


def search_location(graph, query):
    """
    Uses Binary Search (O(log N)) to check whether a location exists in the graph.

    Parameters:
        graph : networkx.Graph
        query : str — location name to find (case-insensitive)

    Returns:
        Matched location name (original casing) if found, else None.
    """
    sorted_locs = get_sorted_locations(graph)
    idx = binary_search_location(sorted_locs, query)
    return sorted_locs[idx] if idx != -1 else None


# ─────────────────────────────────────────────────────────────────────────────
#  PATH STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def compute_path_stats(graph, path):
    """
    Calculates aggregated metrics for a given route.

    Parameters:
        graph : networkx.Graph
        path  : list[str] — ordered sequence of location names

    Returns:
        dict with keys:
            'distance'      — total km (int)
            'travel_time'   — total minutes (int)
            'avg_traffic'   — average traffic level across edges (float)
            'traffic_label' — 'Low' | 'Medium' | 'High'
            'num_stops'     — number of intermediate stops (excluding source/dest)
    """
    if not path or len(path) < 2:
        return {
            'distance': 0, 'travel_time': 0,
            'avg_traffic': 0, 'traffic_label': 'N/A', 'num_stops': 0
        }

    total_dist  = 0
    total_time  = 0
    total_traf  = 0
    num_edges   = len(path) - 1

    for i in range(num_edges):
        edge = graph[path[i]][path[i + 1]]
        total_dist += edge['distance']
        total_time += edge['travel_time']
        total_traf += edge['traffic']

    avg_traffic = total_traf / num_edges

    # Map average traffic level to a human-readable label
    if avg_traffic <= 1.4:
        traffic_label = 'Low'
    elif avg_traffic <= 2.2:
        traffic_label = 'Medium'
    else:
        traffic_label = 'High'

    return {
        'distance':      total_dist,
        'travel_time':   total_time,
        'avg_traffic':   round(avg_traffic, 2),
        'traffic_label': traffic_label,
        'num_stops':     max(0, len(path) - 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  FORMATTING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def format_path_string(path):
    """
    Converts a list of location names into a readable arrow-separated string.

    Example:
        ['Airport', 'Park', 'Hospital'] → 'Airport → Park → Hospital'

    Parameters:
        path : list[str]

    Returns:
        str
    """
    if not path:
        return "No route found."
    return "  →  ".join(path)


def format_time(minutes):
    """
    Converts a raw minute count into a human-friendly duration string.

    Examples:
        5  → '5 min'
        75 → '1 hr 15 min'

    Parameters:
        minutes : int or float

    Returns:
        str
    """
    minutes = int(minutes)
    if minutes < 60:
        return f"{minutes} min"
    hours, mins = divmod(minutes, 60)
    return f"{hours} hr {mins} min" if mins else f"{hours} hr"


# ─────────────────────────────────────────────────────────────────────────────
#  PREFERENCE → WEIGHT MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def weight_from_preference(preference):
    """
    Translates a user-selected route preference label into the corresponding
    NetworkX edge attribute key used as the optimisation weight.

    Parameters:
        preference : str — one of the dropdown options shown in the GUI

    Returns:
        Edge weight key string: 'distance' | 'travel_time' | 'traffic'
    """
    mapping = {
        "Shortest Distance": "distance",
        "Fastest Route":     "travel_time",
        "Low Traffic":       "traffic",
    }
    return mapping.get(preference, "distance")


def get_algorithm_description(algo_name):
    """
    Returns a brief description of an algorithm for display in the GUI status bar.

    Parameters:
        algo_name : str — 'Dijkstra' | 'A* Search' | 'Greedy Best-First'

    Returns:
        str description
    """
    descriptions = {
        "Dijkstra":          "Optimal guaranteed — explores all directions equally",
        "A* Search":         "Optimal + heuristic guided — faster than Dijkstra",
        "Greedy Best-First": "Fastest execution — not guaranteed optimal",
    }
    return descriptions.get(algo_name, "")
