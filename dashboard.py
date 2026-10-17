import tkinter as tk
from tkinter import ttk
import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DashboardTab:
    def __init__(self, parent, api_base):
        self.api_base = api_base
        self.tab = tk.Frame(parent, bg="#f0f0f0")
        self.build_ui()

    def build_ui(self):
        # Title
        tk.Label(self.tab, text="Barangay Dashboard", font=("Segoe UI", 24, "bold"), bg="#f0f0f0").pack(pady=20)

        # === KPI CARDS FRAME ===
        cards_frame = tk.Frame(self.tab, bg="#f0f0f0")
        cards_frame.pack(fill="x", padx=20)

        # Helper to make cards
        def make_card(parent, title, value_var, color):
            frame = tk.Frame(parent, bg=color, padx=20, pady=20)
            frame.pack(side="left", expand=True, fill="both", padx=10)
            tk.Label(frame, text=title, bg=color, fg="white", font=("Arial", 12)).pack(anchor="w")
            tk.Label(frame, textvariable=value_var, bg=color, fg="white", font=("Arial", 24, "bold")).pack(anchor="w")

        self.var_pop = tk.StringVar(value="0")
        self.var_voters = tk.StringVar(value="0")
        self.var_cases = tk.StringVar(value="0")

        make_card(cards_frame, "Total Population", self.var_pop, "#2196F3")  # Blue
        make_card(cards_frame, "Registered Voters", self.var_voters, "#4CAF50")  # Green
        make_card(cards_frame, "Active Cases", self.var_cases, "#F44336")  # Red

        # === CHARTS FRAME ===
        charts_frame = tk.Frame(self.tab, bg="#f0f0f0")
        charts_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Place for Pie Chart
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.plot = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Refresh Button
        tk.Button(self.tab, text="Refresh Data", command=self.load_data, font=("Arial", 12)).pack(pady=10)

        # Load initial data
        self.load_data()

    def load_data(self):
        try:
            # 1. Get Residents for Stats
            res = requests.get(f"{self.api_base}/residents")
            residents = res.json()

            total_pop = len(residents)
            voters = len([r for r in residents if r.get('voter_status') == 'Voter'])
            males = len([r for r in residents if r.get('gender') == 'Male'])
            females = len([r for r in residents if r.get('gender') == 'Female'])

            # 2. Get Blotters
            b_res = requests.get(f"{self.api_base}/blotters")
            blotters = b_res.json()
            total_cases = len(blotters)

            # Update Text
            self.var_pop.set(str(total_pop))
            self.var_voters.set(str(voters))
            self.var_cases.set(str(total_cases))

            # Update Chart (Gender Ratio)
            self.plot.clear()
            self.plot.pie([males, females], labels=['Male', 'Female'], autopct='%1.1f%%', colors=['#36A2EB', '#FF6384'])
            self.plot.set_title("Population by Gender")
            self.canvas.draw()

        except Exception as e:
            print(f"Dashboard error: {e}")