# =============================================================================
#  traffic_simulation.py — Dynamic Traffic Engine
#
#  Simulates real-world traffic fluctuations:
#    • Randomly changes congestion levels across all road edges
#    • Recomputes travel times based on new traffic levels
#    • Provides color-coding utilities for visualization
#    • Enables automatic rerouting when conditions change
# =============================================================================

import random


# ─── Traffic Level Constants ──────────────────────────────────────────────────
TRAFFIC_LOW    = 1    # Clear roads — ideal driving conditions
TRAFFIC_MEDIUM = 2    # Moderate congestion — slight delays expected
TRAFFIC_HIGH   = 3    # Heavy congestion — significant delays

TRAFFIC_LABELS = {
    TRAFFIC_LOW:    "Low",
    TRAFFIC_MEDIUM: "Medium",
    TRAFFIC_HIGH:   "High",
}

# Travel time multipliers per traffic level
# (Base time = distance ÷ 40 km/h × 60 min)
TRAFFIC_MULTIPLIERS = {
    TRAFFIC_LOW:    1.0,    # No delay
    TRAFFIC_MEDIUM: 1.5,    # 50% slower
    TRAFFIC_HIGH:   2.5,    # 150% slower (2.5× base time)
}

BASE_SPEED_KMH = 40   # Average urban driving speed in open conditions

# Color palette for edges in matplotlib visualization
TRAFFIC_COLORS = {
    TRAFFIC_LOW:    "#2ecc71",   # 🟢 Green  — free flow
    TRAFFIC_MEDIUM: "#f39c12",   # 🟡 Amber  — moderate traffic
    TRAFFIC_HIGH:   "#e74c3c",   # 🔴 Red    — heavy traffic
}


def simulate_traffic_update(graph, change_probability=0.70):
    """
    Randomly reassigns traffic levels and recalculates travel times for all edges.

    Each edge has `change_probability` chance of having its traffic level changed
    to a new random value (1, 2, or 3). Travel time is then recomputed from
    distance and the new traffic multiplier.

    Parameters:
        graph              : networkx.Graph — modified IN-PLACE
        change_probability : float (0–1) — likelihood each edge changes (default 70%)

    Returns:
        changes : list of (node_u, node_v, new_traffic_level) for changed edges
    """
    changes = []

    for u, v, data in graph.edges(data=True):
        old_traffic = data['traffic']

        # Roll the dice — should this edge's traffic change?
        if random.random() < change_probability:
            # Pick a new traffic level; allow it to be the same as before
            new_traffic = random.choices(
                [TRAFFIC_LOW, TRAFFIC_MEDIUM, TRAFFIC_HIGH],
                weights=[3, 4, 3],          # Slightly bias toward medium traffic
                k=1
            )[0]

            data['traffic'] = new_traffic

            # Recompute travel time: base_minutes × congestion_multiplier
            base_minutes = (data['distance'] / BASE_SPEED_KMH) * 60
            data['travel_time'] = max(1, round(base_minutes * TRAFFIC_MULTIPLIERS[new_traffic]))

            if new_traffic != old_traffic:
                changes.append((u, v, new_traffic))

    return changes


def get_edge_color(traffic_level):
    """
    Maps a traffic level integer to its matplotlib display color.

    Parameters:
        traffic_level : int — 1 (low), 2 (medium), or 3 (high)

    Returns:
        Hex color string.
    """
    return TRAFFIC_COLORS.get(traffic_level, "#95a5a6")  # gray fallback


def get_traffic_label(traffic_level):
    """
    Returns a human-readable string for a traffic level.

    Parameters:
        traffic_level : int

    Returns:
        'Low' | 'Medium' | 'High'
    """
    return TRAFFIC_LABELS.get(traffic_level, "Unknown")


def get_traffic_summary(graph):
    """
    Counts how many edges fall into each traffic category.

    Parameters:
        graph : networkx.Graph

    Returns:
        dict : {'Low': int, 'Medium': int, 'High': int}
    """
    summary = {'Low': 0, 'Medium': 0, 'High': 0}
    for _, _, data in graph.edges(data=True):
        label = TRAFFIC_LABELS.get(data.get('traffic', 1), 'Low')
        summary[label] += 1
    return summary


def set_edge_traffic(graph, node_u, node_v, new_level):
    """
    Manually sets the traffic level on a specific edge and updates travel time.

    Parameters:
        graph    : networkx.Graph — modified in-place
        node_u   : First endpoint of the edge
        node_v   : Second endpoint of the edge
        new_level: int — 1, 2, or 3

    Raises:
        ValueError if edge doesn't exist or level is invalid.
    """
    if not graph.has_edge(node_u, node_v):
        raise ValueError(f"Edge ({node_u}, {node_v}) does not exist in graph.")
    if new_level not in TRAFFIC_MULTIPLIERS:
        raise ValueError(f"Traffic level must be 1, 2, or 3 — got {new_level}.")

    data = graph[node_u][node_v]
    data['traffic'] = new_level
    base_minutes = (data['distance'] / BASE_SPEED_KMH) * 60
    data['travel_time'] = max(1, round(base_minutes * TRAFFIC_MULTIPLIERS[new_level]))
