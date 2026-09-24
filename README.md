# 🗺 Smart Route Planner — AI Navigation System

> A Python-based AI navigation system that finds optimal routes between city locations using graph algorithms, with a live interactive GUI and dynamic traffic simulation.

---

## 📋 Project Overview

Smart Route Planner models a city as a weighted graph where **nodes** represent locations (Airport, Hospital, Mall, etc.) and **edges** represent roads carrying three attributes:

| Attribute     | Description                              |
|---------------|------------------------------------------|
| `distance`    | Road length in kilometres                |
| `traffic`     | Congestion level — 1=Low, 2=Med, 3=High  |
| `travel_time` | Estimated travel time in minutes         |

Users select a **source**, **destination**, **route preference** (shortest / fastest / low-traffic) and **algorithm**, then visualise the optimal path on a colour-coded live map. A traffic simulation button randomly updates congestion and triggers automatic rerouting.

---

## 🗂 Folder Structure

```
smart_route_planner/
├── main.py               ← Entry point — run this file
├── gui.py                ← Tkinter GUI + Matplotlib visualisation
├── graph_data.py         ← City graph: 14 nodes, 24 edges
├── algorithms.py         ← Dijkstra, A*, Greedy, Binary Search
├── traffic_simulation.py ← Dynamic traffic engine
├── utils.py              ← Shared helpers (stats, formatting, search)
├── requirements.txt      ← Python dependencies
└── README.md             ← This file
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Steps

```bash
# 1. Clone or download the project folder
cd smart_route_planner

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

---

## 📦 Required Libraries

| Library      | Version  | Purpose                                    |
|--------------|----------|--------------------------------------------|
| `networkx`   | ≥ 3.0    | Graph creation, storage, and drawing       |
| `matplotlib` | ≥ 3.7    | Graph visualisation embedded in Tkinter    |
| `tkinter`    | built-in | GUI framework (ships with Python)          |
| `heapq`      | built-in | Min-heap priority queue for algorithms     |
| `math`       | built-in | Euclidean distance heuristic               |
| `random`     | built-in | Random traffic simulation                  |

---

## 🚀 How to Run

```bash
python main.py
```

### GUI Workflow

1. **Select Source Location** — pick a starting city node from the dropdown
2. **Select Destination** — pick the target location
3. **Choose Route Preference**:
   - `Shortest Distance` — minimise total km
   - `Fastest Route` — minimise total minutes
   - `Low Traffic` — minimise congestion level
4. **Choose Algorithm** — Dijkstra / A* Search / Greedy Best-First
5. Click **🔍 Find Optimal Route** — the path is highlighted cyan on the map
6. Click **🚦 Simulate Traffic Update** — traffic changes randomly; if a route exists, it reroutes automatically
7. Click **↺ Reset** — clears the route

---

## 🏙 City Graph

The graph contains **14 locations** and **24 roads**:

```
Nodes: Airport, Park, Hospital, Stadium, Museum,
       Old Town, Central Hub, Mall, Harbor,
       University, Station, Tech Park,
       Suburb, Suburb West
```

Traffic levels are colour-coded on the map:
- 🟢 **Green** — Low traffic (×1.0 travel time)
- 🟡 **Amber** — Medium traffic (×1.5 travel time)
- 🔴 **Red** — High traffic (×2.5 travel time)
- 🔵 **Cyan** — Selected route (overlaid colour)

---

## 🧮 Algorithm Explanations

### 1. Dijkstra's Algorithm
**Time Complexity:** O((V + E) log V)  
**Space Complexity:** O(V)

The classic shortest-path algorithm. Maintains a min-heap of `(cost, node)` pairs. Always expands the lowest-cost unvisited node, relaxing its neighbours. Guarantees the **optimal** path for any non-negative edge weights. Does not use a heuristic — it searches outward in all directions equally.

```
Best for: Guaranteed optimal paths when heuristic is unavailable.
```

---

### 2. A* Search Algorithm
**Time Complexity:** O(E log V) with admissible heuristic  
**Space Complexity:** O(V)

Extends Dijkstra by adding a heuristic function `h(n)` that estimates the remaining distance to the goal (Euclidean distance between grid positions). Each node is ordered by `f(n) = g(n) + h(n)`:

- `g(n)` = actual cost from source to node n
- `h(n)` = estimated cost from n to target (never overestimates → **admissible**)

Because it's guided toward the goal, A* visits fewer nodes than Dijkstra and is both **optimal** and **complete**.

```
Best for: Optimal routes when a spatial layout/heuristic is available.
```

---

### 3. Greedy Best-First Search
**Time Complexity:** O(E log V) worst case  
**Space Complexity:** O(V)

Uses only the heuristic `h(n)` — the `g(n)` cost-so-far is completely ignored. Always expands the node that *looks* closest to the goal. Very fast but **not guaranteed to find the optimal path** — it can be misled by the heuristic into suboptimal routes.

```
Best for: Fast approximate routes when speed matters more than optimality.
```

---

### 4. Binary Search (Location Finder)
**Time Complexity:** O(log N)  
**Space Complexity:** O(1)

Applied to the alphabetically sorted list of city locations. Repeatedly halves the search interval by comparing the query against the middle element. Used internally to verify that a typed location name exists in the graph.

```
Best for: Fast lookup in sorted collections.
```

---

## 📸 Sample Screenshots

*(Place screenshots here after running the application)*

| Screenshot | Description |
|-----------|-------------|
| `screenshot_idle.png` | Application on startup — full city graph with traffic colours |
| `screenshot_route.png` | Optimal route highlighted (cyan) from Airport to Suburb West |
| `screenshot_traffic.png` | After traffic simulation — rerouted path |

---

## 🔮 Future Enhancements

| Feature | Description |
|---------|-------------|
| Real GPS Data | Import real city maps via OpenStreetMap / OSMnx |
| Turn-by-turn Directions | Step-by-step textual navigation instructions |
| Multiple Route Comparison | Show top-3 routes simultaneously |
| Live API Traffic | Connect to Google Maps / TomTom traffic API |
| Animated Route Playback | Animate a vehicle moving along the path |
| Save/Load Map | Persist custom city graphs to JSON |
| Dijkstra vs A* Benchmarking | Side-by-side execution time comparison |
| Directed Graph Support | One-way streets and restricted turns |

---

## 👨‍💻 Tech Stack

- **Python 3.9+**
- **Tkinter** — GUI framework
- **NetworkX** — Graph data structure and algorithms
- **Matplotlib** — Graph rendering embedded in Tkinter
- **heapq** — Priority queue for pathfinding algorithms

---

## 📚 Educational Notes

This project is designed as a **college mini project** to demonstrate:

- **Graph Theory** — modelling real-world networks as weighted graphs
- **Algorithm Design** — Dijkstra vs A* vs Greedy trade-offs
- **Time/Space Complexity** analysis
- **Heuristic Search** — admissibility and optimality
- **Dynamic Systems** — traffic simulation and reactive rerouting
- **GUI Programming** — embedding matplotlib in Tkinter
- **Modular Python** — clean separation of concerns across files

---

*Smart Route Planner — AI Navigation System | College Mini Project*
