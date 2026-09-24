# =============================================================================
#  gui.py — Smart Route Planner  |  Tkinter + Matplotlib Interface
#
#  Builds the complete GUI:
#    • Left panel  : Route controls, dropdowns, result cards, legend
#    • Right panel : Matplotlib city graph canvas
#    • Actions     : Find Route, Simulate Traffic (with auto-reroute)
#    • Visualization: Nodes coloured by role, edges coloured by traffic level
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox

import networkx as nx
import matplotlib
matplotlib.use('TkAgg')                           # Embed matplotlib in Tkinter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from graph_data         import create_city_graph
from algorithms         import dijkstra, astar, greedy_best_first
from traffic_simulation import simulate_traffic_update, get_edge_color, get_traffic_summary
from utils              import (get_sorted_locations, compute_path_stats,
                                format_path_string, format_time,
                                weight_from_preference, get_algorithm_description)


# ─── Colour Palette (Dark Theme) ─────────────────────────────────────────────
BG_ROOT    = "#0f1117"   # Window background
BG_PANEL   = "#1a1f2e"   # Left panel background
BG_CARD    = "#242938"   # Card/widget background
BG_INPUT   = "#2d3347"   # Combobox / input background
LINE_SEP   = "#2a3050"   # Separator line colour

ACE_BLUE   = "#4a9eff"   # Accent blue — headings, borders
ACE_GREEN  = "#48d18a"   # Accent green — source node, success
ACE_RED    = "#ff6b6b"   # Accent red   — destination node, warning
ACE_YLW    = "#ffc94d"   # Accent yellow — medium-traffic highlight
ACE_CYAN   = "#00d4ff"   # Selected-route edge colour

TXT_HEAD   = "#e8eaf6"   # Heading text
TXT_BODY   = "#b0bec5"   # Body / label text
TXT_DIM    = "#546e7a"   # Dimmed / secondary text
TXT_VAL    = "#ffffff"   # Value text

BTN_FIND   = "#1565c0"   # Find-route button background
BTN_TRAF   = "#e65100"   # Traffic button background
BTN_RESET  = "#263238"   # Reset button background


class SmartRoutePlannerApp:
    """
    Main application class.
    Owns the graph data, all widgets, and the matplotlib figure.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_root()

        # ── Core data ────────────────────────────────────────────────────────
        self.graph, self.positions = create_city_graph()
        self.locations    = get_sorted_locations(self.graph)
        self.current_path = []          # Last computed route (list of node names)

        # ── Build UI sections ────────────────────────────────────────────────
        self._build_header()
        self._build_body()              # creates left panel + right canvas

        # ── Initial draw ─────────────────────────────────────────────────────
        self._draw_graph()

    # =========================================================================
    #  ROOT WINDOW SETUP
    # =========================================================================

    def _configure_root(self):
        self.root.title("Smart Route Planner — AI Navigation System")
        self.root.configure(bg=BG_ROOT)
        self.root.minsize(1450, 800)
        # Maximise window cross-platform
        try:
            self.root.state('zoomed')          # Windows
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)  # Linux
            except tk.TclError:
                self.root.geometry("1400x850")

    # =========================================================================
    #  HEADER BAR
    # =========================================================================

    def _build_header(self):
        """Slim title bar across the top."""
        bar = tk.Frame(self.root, bg="#0d1526", height=52)
        bar.pack(fill='x', side='top')
        bar.pack_propagate(False)

        # App title
        tk.Label(
            bar,
            text="  🗺   Smart Route Planner",
            font=("Segoe UI", 16, "bold"),
            fg=ACE_BLUE, bg="#0d1526", pady=10
        ).pack(side='left', padx=8)

        # Sub-caption
        tk.Label(
            bar,
            text="AI Navigation System  |  Dijkstra  •  A*  •  Greedy  •  Binary Search",
            font=("Segoe UI", 10),
            fg=TXT_DIM, bg="#0d1526"
        ).pack(side='left', padx=4)

        # Traffic summary label (updated after each simulation)
        self.traffic_summary_var = tk.StringVar(value="")
        tk.Label(
            bar, textvariable=self.traffic_summary_var,
            font=("Segoe UI", 9), fg=TXT_BODY, bg="#0d1526"
        ).pack(side='right', padx=16)

    # =========================================================================
    #  BODY (LEFT PANEL + RIGHT CANVAS)
    # =========================================================================

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG_ROOT)
        body.pack(fill='both', expand=True)

        # ── Left control panel (fixed width) ─────────────────────────────────
        self.left_panel = tk.Frame(body, bg=BG_PANEL, width=380)
        self.left_panel.pack(side='left', fill='y')
        self.left_panel.pack_propagate(False)
        self._build_left_panel(self.left_panel)

        # Thin vertical divider
        tk.Frame(body, bg=LINE_SEP, width=2).pack(side='left', fill='y')

        # ── Right graph area (expands to fill remaining space) ────────────────
        right = tk.Frame(body, bg=BG_ROOT)
        right.pack(side='left', fill='both', expand=True)
        self._build_graph_canvas(right)

    # =========================================================================
    #  LEFT CONTROL PANEL
    # =========================================================================

    def _build_left_panel(self, parent):
        # Scrollable inner frame so controls don't clip on small screens
        canvas = tk.Canvas(parent, bg=BG_PANEL, highlightthickness=0)
        scroll = tk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = tk.Frame(canvas, bg=BG_PANEL)
        win_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(win_id, width=e.width)

        inner.bind('<Configure>', _resize)

        # ── Sections ─────────────────────────────────────────────────────────
        self._section(inner, "⚙   Route Configuration")
        self._build_route_controls(inner)

        self._section(inner, "🔢  Algorithm Selection")
        self._build_algo_controls(inner)

        self._section(inner, "🔍  Find & Simulate")
        self._build_action_buttons(inner)

        self._section(inner, "📊  Route Statistics")
        self._build_result_card(inner)

        self._section(inner, "🛣   Optimal Path")
        self._build_path_display(inner)

        self._section(inner, "🎨  Map Legend")
        self._build_legend(inner)

    # ── Route Configuration ───────────────────────────────────────────────────

    def _build_route_controls(self, parent):
        self._label(parent, "Source Location")
        self.src_var = tk.StringVar(value=self.locations[0])
        self._combobox(parent, self.src_var, self.locations)

        self._label(parent, "Destination Location")
        self.dst_var = tk.StringVar(value=self.locations[-1])
        self._combobox(parent, self.dst_var, self.locations)

        self._label(parent, "Route Preference")
        self.pref_var = tk.StringVar(value="Shortest Distance")
        self._combobox(parent, self.pref_var,
                       ["Shortest Distance", "Fastest Route", "Low Traffic"])


    # ── Algorithm Selection ───────────────────────────────────────────────────

    def _build_algo_controls(self, parent):
        self._label(parent, "Algorithm")
        self.algo_var = tk.StringVar(value="Dijkstra")

        self._combobox(
            parent,
            self.algo_var,
            ["Dijkstra", "A* Search", "Greedy Best-First"]
        )

        self.algo_desc_var = tk.StringVar(
            value=get_algorithm_description("Dijkstra")
        )

        tk.Label(
            parent,
            textvariable=self.algo_desc_var,
            font=("Segoe UI", 10, "bold"),
            fg=TXT_DIM,
            bg=BG_PANEL,
            wraplength=270,
            justify='left'
        ).pack(fill='x', padx=14, pady=(0, 6))

        # Update description when algorithm changes
        self.algo_var.trace_add(
            'write',
            lambda *_: self.algo_desc_var.set(
                get_algorithm_description(self.algo_var.get())
            )
        )

    # ── Action Buttons ────────────────────────────────────────────────────────

    def _build_action_buttons(self, parent):
        btn_frame = tk.Frame(parent, bg=BG_PANEL)
        btn_frame.pack(fill='x', padx=14, pady=6)

        tk.Button(
            btn_frame,
            text="🔍  Find Optimal Route",
            command=self._find_route,
            bg=BTN_FIND,
            fg=TXT_HEAD,
            font=("Segoe UI", 11, "bold"),
            relief='flat',
            cursor='hand2',
            activebackground="#1976d2",
            activeforeground='white',
            pady=9,
            padx=6
        ).pack(fill='x', pady=(0, 6))

        tk.Button(
            btn_frame,
            text="🚦  Simulate Traffic Update",
            command=self._simulate_traffic,
            bg=BTN_TRAF,
            fg=TXT_HEAD,
            font=("Segoe UI", 11, "bold"),
            relief='flat',
            cursor='hand2',
            activebackground="#bf360c",
            activeforeground='white',
            pady=9,
            padx=6
        ).pack(fill='x', pady=(0, 6))

        tk.Button(
            btn_frame,
            text="↺  Reset / Clear Route",
            command=self._reset,
            bg=BTN_RESET,
            fg=TXT_BODY,
            font=("Segoe UI", 9),
            relief='flat',
            cursor='hand2',
            activebackground="#37474f",
            activeforeground='white',
            pady=7
        ).pack(fill='x')
    # ── Result Statistics Card ────────────────────────────────────────────────

    def _build_result_card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD, bd=0,
                        highlightbackground=LINE_SEP, highlightthickness=1)
        card.pack(fill='x', padx=14, pady=6)

        self.result_vars = {}
        rows = [
            ("Algorithm",       "algo",     ACE_BLUE),
            ("Preference",      "pref",     TXT_BODY),
            ("Total Distance",  "distance", ACE_GREEN),
            ("Travel Time",     "time",     ACE_YLW),
            ("Traffic Level",   "traffic",  ACE_RED),
            ("Stops (via)",     "stops",    TXT_BODY),
        ]
        for label, key, color in rows:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill='x', padx=12, pady=4)
            tk.Label(row, text=label + ":",
                     font=("Segoe UI", 9), fg=TXT_DIM,
                     bg=BG_CARD, width=15, anchor='w').pack(side='left')
            var = tk.StringVar(value="—")
            self.result_vars[key] = var
            tk.Label(row, textvariable=var,
                     font=("Segoe UI", 9, "bold"), fg=color,
                     bg=BG_CARD).pack(side='left')

    # ── Path Display ──────────────────────────────────────────────────────────

    def _build_path_display(self, parent):
        self.path_text = tk.Text(
            parent, height=6, bg=BG_CARD, fg=ACE_GREEN,
            font=("Consolas", 8), relief='flat',
            wrap='word', padx=10, pady=8,
            insertbackground=ACE_GREEN,
            highlightbackground=LINE_SEP, highlightthickness=1
        )
        self.path_text.pack(fill='x', padx=14, pady=6)
        self._set_path_text("Select source and destination,\nthen click Find Optimal Route.")

    # ── Legend ────────────────────────────────────────────────────────────────

    def _build_legend(self, parent):
        legend_frame = tk.Frame(parent, bg=BG_PANEL)
        legend_frame.pack(fill='x', padx=14, pady=4)

        items = [
            ("#2ecc71", "Low Traffic (roads clear)"),
            ("#f39c12", "Medium Traffic (moderate)"),
            ("#e74c3c", "High Traffic (heavy delay)"),
            (ACE_CYAN,  "Selected Route"),
            (ACE_GREEN, "Source Node"),
            (ACE_RED,   "Destination Node"),
            ("#90cdf4", "Intermediate Stop"),
        ]
        for color, label in items:
            row = tk.Frame(legend_frame, bg=BG_PANEL)
            row.pack(fill='x', pady=2)
            tk.Label(row, bg=color, width=3, relief='flat').pack(side='left', padx=(0, 8))
            tk.Label(row, text=label, fg=TXT_BODY, bg=BG_PANEL,
                     font=("Segoe UI", 8)).pack(side='left')

        tk.Frame(parent, height=16, bg=BG_PANEL).pack()   # bottom padding

    # =========================================================================
    #  RIGHT GRAPH CANVAS
    # =========================================================================

    def _build_graph_canvas(self, parent):
        header = tk.Frame(parent, bg=BG_ROOT, pady=4)
        header.pack(fill='x', padx=12)
        tk.Label(header, text="City Road Network — Live Traffic Visualization",
                 font=("Segoe UI", 11, "bold"),
                 fg=TXT_BODY, bg=BG_ROOT).pack(side='left')

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(header, textvariable=self.status_var,
                 font=("Segoe UI", 9, "italic"),
                 fg=TXT_DIM, bg=BG_ROOT).pack(side='right')

        # Matplotlib figure embedded in Tkinter
        self.fig, self.ax = plt.subplots(figsize=(11, 7))
        self.fig.patch.set_facecolor("#0f1117")
        self.ax.set_facecolor("#0f1117")

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True,
                                         padx=10, pady=(0, 10))

    # =========================================================================
    #  WIDGET HELPERS
    # =========================================================================

    def _section(self, parent, text):
        """Draws a coloured section header with a separator line."""
        
        tk.Frame(parent, bg=BG_PANEL, height=8).pack()

        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 9, "bold"),
            fg=ACE_BLUE,
            bg=BG_PANEL,
            anchor='w',
            padx=14,
            pady=4
        ).pack(fill='x')

        tk.Frame(
            parent,
            bg=LINE_SEP,
            height=1
        ).pack(fill='x', padx=14)

    def _label(self, parent, text):
        tk.Label(parent, text=text,
                 font=("Segoe UI", 9), fg=TXT_DIM,
                 bg=BG_PANEL, anchor='w').pack(fill='x', padx=14, pady=(6, 1))

    def _combobox(self, parent, var, values):
        """Dark-styled ttk Combobox."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Nav.TCombobox',
                         fieldbackground=BG_INPUT,
                         background=BG_INPUT,
                         foreground=TXT_HEAD,
                         selectbackground=BG_INPUT,
                         selectforeground=TXT_HEAD,
                         arrowcolor=ACE_BLUE,
                         bordercolor=LINE_SEP,
                         lightcolor=BG_INPUT,
                         darkcolor=BG_INPUT)
        style.map('Nav.TCombobox',
                  fieldbackground=[('readonly', BG_INPUT)],
                  selectbackground=[('readonly', BG_INPUT)])
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          style='Nav.TCombobox', state='readonly',
                          font=("Segoe UI", 9))
        cb.pack(fill='x', padx=14, pady=(0, 4))
        return cb

    def _set_path_text(self, text):
        self.path_text.config(state='normal')
        self.path_text.delete('1.0', 'end')
        self.path_text.insert('end', text)
        self.path_text.config(state='disabled')

    # =========================================================================
    #  CORE LOGIC — Find Route
    # =========================================================================

    def _find_route(self):
        """
        Reads UI selections → runs chosen algorithm → updates result panel
        and redraws the graph with the highlighted optimal path.
        """
        src  = self.src_var.get()
        dst  = self.dst_var.get()
        algo = self.algo_var.get()
        pref = self.pref_var.get()

        # ── Input validation ─────────────────────────────────────────────────
        if src == dst:
            messagebox.showwarning("Invalid Selection",
                                   "Source and destination must be different locations.")
            return

        weight = weight_from_preference(pref)

        # ── Run selected algorithm ────────────────────────────────────────────
        self.status_var.set(f"Computing route with {algo}…")
        self.root.update_idletasks()

        try:
            if algo == "Dijkstra":
                path, cost = dijkstra(self.graph, src, dst, weight)
            elif algo == "A* Search":
                path, cost = astar(self.graph, src, dst, weight, self.positions)
            else:   # Greedy Best-First
                path, cost = greedy_best_first(self.graph, src, dst, weight, self.positions)

        except Exception as err:
            messagebox.showerror("Algorithm Error", f"An error occurred:\n{err}")
            self.status_var.set("Error during route computation.")
            return

        # ── Handle no-path result ─────────────────────────────────────────────
        if not path:
            messagebox.showinfo("No Route Found",
                                f"No path exists between\n{src}  →  {dst}")
            self.status_var.set("No route found.")
            return

        # ── Store and display result ──────────────────────────────────────────
        self.current_path = path
        stats = compute_path_stats(self.graph, path)

        self.result_vars['algo'].set(algo)
        self.result_vars['pref'].set(pref)
        self.result_vars['distance'].set(f"{stats['distance']} km")
        self.result_vars['time'].set(format_time(stats['travel_time']))
        self.result_vars['traffic'].set(stats['traffic_label'])
        self.result_vars['stops'].set(
            str(stats['num_stops']) + (" stop" if stats['num_stops'] == 1 else " stops"))

        # Display path as readable string
        self._set_path_text(format_path_string(path))

        self.status_var.set(
            f"Route found — {stats['distance']} km  |  {format_time(stats['travel_time'])}  |  "
            f"{len(path) - 1} roads")

        # ── Redraw graph with highlighted route ───────────────────────────────
        self._draw_graph(path)

    # =========================================================================
    #  CORE LOGIC — Simulate Traffic
    # =========================================================================

    def _simulate_traffic(self):
        """
        Triggers random traffic changes across all edges.
        If a route was previously calculated, automatically reroutes.
        """
        self.status_var.set("Simulating traffic changes…")
        self.root.update_idletasks()

        simulate_traffic_update(self.graph)

        # Update header summary
        summary = get_traffic_summary(self.graph)
        self.traffic_summary_var.set(
            f"🟢 Low: {summary['Low']}   🟡 Medium: {summary['Medium']}   "
            f"🔴 High: {summary['High']}")

        if self.current_path:
            # Reroute with same settings after traffic change
            self._find_route()
            self.status_var.set("Traffic updated — route recalculated automatically.")
        else:
            # Just redraw the graph with new traffic colours
            self._draw_graph()
            self.status_var.set("Traffic updated — select a route to see impact.")

    # =========================================================================
    #  CORE LOGIC — Reset
    # =========================================================================

    def _reset(self):
        """Clears the current route and resets the display."""
        self.current_path = []
        for var in self.result_vars.values():
            var.set("—")
        self._set_path_text("Route cleared. Select source and destination.")
        self.status_var.set("Ready")
        self._draw_graph()

    # =========================================================================
    #  GRAPH VISUALIZATION
    # =========================================================================

    def _draw_graph(self, highlighted_path=None):
        """
        Renders the city graph on the matplotlib axes embedded in Tkinter.

        Edge colours reflect current traffic:
            🟢 Green  — Low traffic
            🟡 Amber  — Medium traffic
            🔴 Red    — High traffic
            🔵 Cyan   — Selected route (overrides traffic colour)

        Node colours reflect role in current route:
            🟢 Green  — Source
            🔴 Red    — Destination
            🔵 Blue   — Intermediate waypoint
            ⬛ Gray   — Unvisited
        """
        self.ax.clear()
        self.ax.set_facecolor("#0f1117")

        pos = self.positions   # {node_name: (x, y)}

        # ── Build path edge set for fast lookup ───────────────────────────────
        path_edges = set()
        if highlighted_path and len(highlighted_path) > 1:
            for i in range(len(highlighted_path) - 1):
                u, v = highlighted_path[i], highlighted_path[i + 1]
                path_edges.add((u, v))
                path_edges.add((v, u))

        # ── Compute per-edge colour and width ─────────────────────────────────
        edge_colors = []
        edge_widths = []
        edge_alphas = []

        for u, v, data in self.graph.edges(data=True):
            if (u, v) in path_edges:
                edge_colors.append(ACE_CYAN)     # Selected route = cyan
                edge_widths.append(5.0)
                edge_alphas.append(0.95)
            else:
                traf_color = get_edge_color(data.get('traffic', 1))
                edge_colors.append(traf_color)
                # Slightly dim non-route edges when a path is shown
                edge_widths.append(1.8 if highlighted_path else 2.0)
                edge_alphas.append(0.55 if highlighted_path else 0.85)

        # ── Draw edges ────────────────────────────────────────────────────────
        # Matplotlib's draw_networkx_edges doesn't support per-edge alpha,
        # so we draw route edges separately for full opacity.
        if path_edges:
            non_path_edges = [(u, v) for u, v in self.graph.edges()
                              if (u, v) not in path_edges]
            path_edge_list = [(u, v) for u, v in self.graph.edges()
                              if (u, v) in path_edges]

            # Background (non-route) edges — dimmed
            non_colors = []
            non_widths = []
            for u, v in non_path_edges:
                d = self.graph[u][v]
                non_colors.append(get_edge_color(d.get('traffic', 1)))
                non_widths.append(1.6)
            if non_path_edges:
                nx.draw_networkx_edges(self.graph, pos, ax=self.ax,
                                       edgelist=non_path_edges,
                                       edge_color=non_colors, width=non_widths,
                                       alpha=0.45)

            # Route edges — bright cyan, thick
            if path_edge_list:
                nx.draw_networkx_edges(self.graph, pos, ax=self.ax,
                                       edgelist=path_edge_list,
                                       edge_color=ACE_CYAN, width=5.5,
                                       alpha=0.95,
                                       style='solid')
        else:
            # No route selected — draw all edges with traffic colours
            nx.draw_networkx_edges(self.graph, pos, ax=self.ax,
                                   edge_color=edge_colors, width=edge_widths,
                                   alpha=0.80)

        # ── Edge labels (distance in km) ──────────────────────────────────────
        edge_labels = {(u, v): f"{d['distance']}km"
                       for u, v, d in self.graph.edges(data=True)}
        nx.draw_networkx_edge_labels(
            self.graph, pos, edge_labels=edge_labels, ax=self.ax,
            font_size=6.5, font_color="#8899aa",
            bbox=dict(boxstyle='round,pad=0.15', fc="#1a1f2e",
                      alpha=0.75, ec='none')
        )

        # ── Compute per-node colour and size based on route role ──────────────
        node_colors = []
        node_sizes  = []
        border_colors = []

        path_set = set(highlighted_path) if highlighted_path else set()

        for node in self.graph.nodes():
            if highlighted_path and node == highlighted_path[0]:
                node_colors.append(ACE_GREEN)    # Source
                node_sizes.append(750)
                border_colors.append("#ffffff")
            elif highlighted_path and node == highlighted_path[-1]:
                node_colors.append(ACE_RED)      # Destination
                node_sizes.append(750)
                border_colors.append("#ffffff")
            elif highlighted_path and node in path_set:
                node_colors.append("#90cdf4")    # Intermediate waypoint
                node_sizes.append(520)
                border_colors.append(ACE_CYAN)
            else:
                node_colors.append("#2d3a4a")    # Default
                node_sizes.append(420)
                border_colors.append("#4a6075")

        # ── Draw nodes ────────────────────────────────────────────────────────
        nx.draw_networkx_nodes(
            self.graph, pos, ax=self.ax,
            node_color=node_colors, node_size=node_sizes,
            edgecolors=border_colors, linewidths=1.5
        )

        # ── Draw node labels ──────────────────────────────────────────────────
        nx.draw_networkx_labels(
            self.graph, pos, ax=self.ax,
            font_size=7.5, font_color=TXT_HEAD,
            font_family='sans-serif', font_weight='bold'
        )

        # ── Legend ────────────────────────────────────────────────────────────
        legend_patches = [
            mpatches.Patch(color="#2ecc71", label="Low Traffic"),
            mpatches.Patch(color="#f39c12", label="Medium Traffic"),
            mpatches.Patch(color="#e74c3c", label="High Traffic"),
            mpatches.Patch(color=ACE_CYAN,  label="Selected Route"),
            mpatches.Patch(color=ACE_GREEN, label="Source"),
            mpatches.Patch(color=ACE_RED,   label="Destination"),
        ]
        self.ax.legend(
            handles=legend_patches,
            loc='lower right',
            facecolor="#1a1f2e", edgecolor="#2a3050",
            labelcolor=TXT_BODY, fontsize=8,
            framealpha=0.9
        )

        # ── Title and finalize ────────────────────────────────────────────────
        title = "City Road Network"
        if highlighted_path:
            algo = self.algo_var.get()
            pref = self.pref_var.get()
            title = f"Route: {highlighted_path[0]}  →  {highlighted_path[-1]}   [{algo} | {pref}]"

        self.ax.set_title(title, color="#90cdf4",
                          fontsize=11, fontweight='bold', pad=14)
        self.ax.axis('off')
        self.fig.tight_layout(pad=1.2)
        self.canvas.draw()
