
import tkinter as tk
from gui import SmartRoutePlannerApp

def main():
    """
    Initialises the Tkinter root window and launches the Smart Route Planner.
    All application logic is delegated to SmartRoutePlannerApp in gui.py.
    """
    root = tk.Tk()
    root.minsize(1100, 680)
    app = SmartRoutePlannerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
