# =============================================================================
#  algorithms.py — Pathfinding Algorithms & Search Utilities
#
#  Implements four algorithms used by the Smart Route Planner:
#    1. Dijkstra's Algorithm      — guaranteed optimal, O((V+E) log V)
#    2. A* Search                 — optimal + heuristic-guided, O(E log V)
#    3. Greedy Best-First Search  — fast but not guaranteed optimal, O(E log V)
#    4. Binary Search             — O(log N) location lookup in sorted list
# =============================================================================

import heapq    # Min-heap for priority queues
import math     # sqrt for Euclidean heuristic


# ─────────────────────────────────────────────────────────────────────────────
#  PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _reconstruct_path(prev, source, target):
    """
    Traces the predecessor dictionary backwards from target to source.

    Parameters:
        prev   : dict  {node: predecessor_node}  built during search
        source : Starting node
        target : Goal node

    Returns:
        List of nodes from source → target, or [] if unreachable.
    """
    path = []
    node = target
    # Walk backwards through predecessor chain
    while node is not None:
        path.append(node)
        node = prev.get(node)   # returns None when we reach a node with no predecessor

    path.reverse()

    # Validity check: path must start at source
    return path if (path and path[0] == source) else []


def _path_cost(graph, path, weight):
    """
    Sums the specified edge weight attribute along a full path.

    Parameters:
        graph  : NetworkX graph
        path   : Ordered list of node names
        weight : Edge attribute key ('distance', 'travel_time', 'traffic')

    Returns:
        Total cost (float), or 0 for single-node paths.
    """
    return sum(
        graph[path[i]][path[i + 1]][weight]
        for i in range(len(path) - 1)
    )


def _euclidean_heuristic(positions, node, target):
    """
    Straight-line (Euclidean) distance between two nodes' grid positions.
    Used as the admissible heuristic for A* and the ranking function for Greedy.

    Parameters:
        positions : dict  {node_name: (x, y)}
        node      : Current node
        target    : Goal node

    Returns:
        Float Euclidean distance.
    """
    x1, y1 = positions[node]
    x2, y2 = positions[target]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# ─────────────────────────────────────────────────────────────────────────────
#  ALGORITHM 1 — DIJKSTRA'S ALGORITHM
# ─────────────────────────────────────────────────────────────────────────────
# Time Complexity : O((V + E) log V)  where V = nodes, E = edges
# Space Complexity: O(V)
#
# How it works:
#   Maintains a min-heap of (cost_so_far, node). Always expands the lowest-cost
#   unvisited node. Guarantees the OPTIMAL (minimum-cost) path for non-negative
#   edge weights. It does not use a heuristic — it explores in all directions.
# ─────────────────────────────────────────────────────────────────────────────

def dijkstra(graph, source, target, weight='distance'):
    """
    Finds the shortest/fastest/lowest-traffic path using Dijkstra's Algorithm.

    Parameters:
        graph  : NetworkX graph
        source : Starting location name
        target : Destination location name
        weight : Edge attribute to minimize — 'distance' | 'travel_time' | 'traffic'

    Returns:
        (path: list[str], cost: float)
        path is empty list if no path exists.
    """
    # Initialise all node distances to infinity; source gets 0
    dist = {node: float('inf') for node in graph.nodes()}
    dist[source] = 0
    prev = {}   # predecessor map for path reconstruction

    # Min-heap: each entry is (accumulated_cost, node_name)
    heap = [(0, source)]
    visited = set()

    while heap:
        d, u = heapq.heappop(heap)

        # Skip stale heap entries (a shorter path to u was already found)
        if u in visited:
            continue
        visited.add(u)

        # Early exit: once target is popped from heap, we have the shortest path
        if u == target:
            break

        # Relax all outgoing edges from u
        for v in graph.neighbors(u):
            edge_w = graph[u][v][weight]
            new_dist = dist[u] + edge_w

            if new_dist < dist[v]:          # Found a shorter path to v
                dist[v] = new_dist
                prev[v] = u                 # Record how we reached v
                heapq.heappush(heap, (new_dist, v))

    path = _reconstruct_path(prev, source, target)
    return (path, dist[target]) if path else ([], float('inf'))


# ─────────────────────────────────────────────────────────────────────────────
#  ALGORITHM 2 — A* SEARCH ALGORITHM
# ─────────────────────────────────────────────────────────────────────────────
# Time Complexity : O(E log V) with admissible heuristic (often faster than Dijkstra)
# Space Complexity: O(V)
#
# How it works:
#   Like Dijkstra but each node is prioritised by f(n) = g(n) + h(n), where:
#     g(n) = actual cost from source to n
#     h(n) = estimated cost from n to target (Euclidean heuristic)
#   Because h(n) never overestimates the true cost, A* is both OPTIMAL and
#   COMPLETE. It explores fewer nodes than Dijkstra by steering towards goal.
# ─────────────────────────────────────────────────────────────────────────────

def astar(graph, source, target, weight='distance', positions=None):
    """
    Finds the optimal path using A* Search with Euclidean distance heuristic.

    Parameters:
        graph     : NetworkX graph
        source    : Starting location name
        target    : Destination location name
        weight    : Edge attribute to minimise
        positions : dict {node: (x, y)} for heuristic — loaded from graph if None

    Returns:
        (path: list[str], cost: float)
    """
    if positions is None:
        import networkx as nx
        positions = nx.get_node_attributes(graph, 'pos')

    # g_score[n] = cheapest known cost from source to n
    g_score = {node: float('inf') for node in graph.nodes()}
    g_score[source] = 0
    prev = {}

    # f_score = g + h; used to order the priority queue
    h_start = _euclidean_heuristic(positions, source, target)
    heap = [(h_start, source)]
    visited = set()

    while heap:
        f, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        if u == target:
            break

        for v in graph.neighbors(u):
            edge_w = graph[u][v][weight]
            tentative_g = g_score[u] + edge_w   # cost to reach v through u

            if tentative_g < g_score[v]:
                g_score[v] = tentative_g
                prev[v] = u
                h_v = _euclidean_heuristic(positions, v, target)
                f_score = tentative_g + h_v     # f = g + h
                heapq.heappush(heap, (f_score, v))

    path = _reconstruct_path(prev, source, target)
    return (path, g_score[target]) if path else ([], float('inf'))


# ─────────────────────────────────────────────────────────────────────────────
#  ALGORITHM 3 — GREEDY BEST-FIRST SEARCH
# ─────────────────────────────────────────────────────────────────────────────
# Time Complexity : O(E log V) worst case — often much faster in practice
# Space Complexity: O(V)
#
# How it works:
#   Always expands the node that LOOKS closest to the target (lowest h(n)).
#   It completely ignores the cost already paid (g(n)), making it very fast but
#   NOT guaranteed to find the optimal path — it can be "fooled" by the heuristic.
#   Useful when speed matters more than optimality.
# ─────────────────────────────────────────────────────────────────────────────

def greedy_best_first(graph, source, target, weight='distance', positions=None):
    """
    Finds a path using Greedy Best-First Search (heuristic only, no cost tracking).

    Parameters:
        graph     : NetworkX graph
        source    : Starting location name
        target    : Destination location name
        weight    : Edge attribute used to compute the final reported cost
        positions : dict {node: (x, y)} for heuristic

    Returns:
        (path: list[str], cost: float)  — cost computed after path is found.
    """
    if positions is None:
        import networkx as nx
        positions = nx.get_node_attributes(graph, 'pos')

    prev = {}
    visited = set()

    # Priority is purely the heuristic distance to target — no g(n) tracking
    h_start = _euclidean_heuristic(positions, source, target)
    heap = [(h_start, source)]

    while heap:
        h, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        if u == target:
            break

        for v in graph.neighbors(u):
            if v not in visited:
                prev[v] = u
                h_v = _euclidean_heuristic(positions, v, target)
                heapq.heappush(heap, (h_v, v))  # ordered only by h(v), not g+h

    path = _reconstruct_path(prev, source, target)
    # Compute actual cost along the found path using the selected weight attribute
    cost = _path_cost(graph, path, weight) if path else float('inf')
    return path, cost


# ─────────────────────────────────────────────────────────────────────────────
#  ALGORITHM 4 — BINARY SEARCH  (Location Finder)
# ─────────────────────────────────────────────────────────────────────────────
# Time Complexity : O(log N)  where N = number of locations
# Space Complexity: O(1)
#
# How it works:
#   Requires a SORTED list. Repeatedly halves the search interval by comparing
#   the query against the middle element. Used to quickly check if a typed
#   location name exists in the city graph.
# ─────────────────────────────────────────────────────────────────────────────

def binary_search_location(sorted_locations, query):
    """
    Searches for a location name in an alphabetically sorted list.

    Parameters:
        sorted_locations : list[str]  — must be sorted A→Z
        query            : str        — location to find (case-insensitive)

    Returns:
        int index of the found location, or -1 if not found.
    """
    query_lower = query.strip().lower()
    low, high = 0, len(sorted_locations) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_locations[mid].lower()

        if mid_val == query_lower:
            return mid              # ✓ Found — return index
        elif mid_val < query_lower:
            low = mid + 1           # Query is in the RIGHT half
        else:
            high = mid - 1          # Query is in the LEFT half

    return -1   # Not found
