import tkinter as tk
from tkinter import ttk, messagebox
import requests

COLORS = {
    "bg_main": "#F0F2F5",
    "bg_card": "#FFFFFF",
    "primary": "#1877F2",
    "secondary": "#42B72A",
    "danger": "#FF3B30",
    "text_dark": "#1C1E21",
    "text_light": "#65676B",
    "border": "#DDDFE2"
}


class OfficialsTab:
    def __init__(self, parent, api_base, user_session):
        self.parent = parent
        self.api_base = api_base
        self.user_session = user_session
        self.tab = tk.Frame(self.parent, bg=COLORS["bg_main"])

        self.officials_data = []
        self.resident_list = []  # List for dropdowns
        self.entries = {}

        # We need a main container to switch between "View" and "Edit"
        self.main_container = tk.Frame(self.tab, bg=COLORS["bg_main"])
        self.main_container.pack(fill="both", expand=True)

        self.load_officials(initial=True)

    def load_officials(self, initial=False):
        try:
            res = requests.get(f"{self.api_base}/officials")
            res.raise_for_status()
            self.officials_data = res.json()
            if initial:
                self.show_view_mode()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load officials: {e}")
            if initial:
                self.show_view_mode()

    # =========================================================
    # LOAD RESIDENTS (For Dropdown)
    # =========================================================
    def load_residents(self):
        try:
            res = requests.get(f"{self.api_base}/residents")
            res.raise_for_status()
            data = res.json()
            self.resident_list = []
            for r in data:
                # Format: ID - First Last Extension
                ext = r.get("extension", "")
                if ext and ext != "N/A":
                    full = f"{r['id']} - {r['first_name']} {r['last_name']} {ext}"
                else:
                    full = f"{r['id']} - {r['first_name']} {r['last_name']}"
                self.resident_list.append(full)
        except Exception as e:
            print(f"Error loading residents for officials: {e}")
            self.resident_list = []

    # =========================================================
    # VIEW MODE (Hierarchy Chart)
    # =========================================================
    def show_view_mode(self):
        # Clear container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # 1. Header / Toolbar
        header = tk.Frame(self.main_container, bg=COLORS["bg_main"], pady=10, padx=10)
        header.pack(fill="x")

        tk.Label(header, text="Barangay Organizational Chart",
                 font=("Segoe UI", 16, "bold"), bg=COLORS["bg_main"], fg=COLORS["text_dark"]).pack(side="left")

        tk.Button(header, text="Refresh", bg=COLORS["secondary"], fg="white",
                  font=("Segoe UI", 9), padx=10, pady=2, relief="flat",
                  command=lambda: self.load_officials(initial=True)).pack(side="left", padx=15)

        # Only show Edit button if Admin
        if self.user_session.get("role") == "Admin":
            tk.Button(header, text="Edit Officials", bg=COLORS["primary"], fg="white",
                      font=("Segoe UI", 10), padx=15, pady=5, relief="flat",
                      command=self.show_edit_mode).pack(side="right")

        # 2. Scrollable Canvas for the Chart
        canvas = tk.Canvas(self.main_container, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_main"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Center the content loosely
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            canvas.create_window((e.width / 2, 0), window=scrollable_frame, anchor="n")))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- MOUSEWHEEL SCROLLING ---
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # 3. RENDER CARDS
        off_map = {item['position']: item['full_name'] for item in self.officials_data}

        # Helper to draw a card
        def draw_card(parent_frame, title, name, bg_color=COLORS["bg_card"], fg_title=COLORS["text_light"], width=300):
            card = tk.Frame(parent_frame, bg=bg_color, bd=1, relief="solid", padx=10, pady=10)
            tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), fg=fg_title, bg=bg_color).pack()
            tk.Label(card, text=name or "(Vacant)", font=("Segoe UI", 12, "bold"), fg=COLORS["text_dark"], bg=bg_color,
                     wraplength=width - 20).pack(pady=(5, 0))
            return card

        # -- LEVEL 1: CAPTAIN --
        frame_lvl1 = tk.Frame(scrollable_frame, bg=COLORS["bg_main"], pady=20)
        frame_lvl1.pack()
        c_card = draw_card(frame_lvl1, "PUNONG BARANGAY", off_map.get("Barangay Captain", ""),
                           bg_color="#E7F3FF", fg_title=COLORS["primary"], width=350)
        c_card.pack()

        tk.Label(scrollable_frame, text=" ", bg=COLORS["bg_main"], font=("Arial", 14), fg="#AAA").pack()

        # -- LEVEL 2: SECRETARY & TREASURER --
        frame_lvl2 = tk.Frame(scrollable_frame, bg=COLORS["bg_main"], pady=10)
        frame_lvl2.pack()

        # Secretary
        sec_card = draw_card(frame_lvl2, "BARANGAY SECRETARY", off_map.get("Barangay Secretary", ""))
        sec_card.pack(side="left", padx=20)

        # Treasurer
        treas_card = draw_card(frame_lvl2, "BARANGAY TREASURER", off_map.get("Barangay Treasurer", ""))
        treas_card.pack(side="left", padx=20)

        # Connecting Line 2
        tk.Label(scrollable_frame, text=" ", bg=COLORS["bg_main"], font=("Arial", 14), fg="#AAA").pack()
        tk.Label(scrollable_frame, text=" ", bg=COLORS["bg_main"], font=("Arial", 10), fg="#AAA").pack()

        # -- LEVEL 3: KAGAWADS (Grid Layout) --
        tk.Label(scrollable_frame, text="SANGGUNIANG BARANGAY MEMBERS (KAGAWAD)",
                 font=("Segoe UI", 10, "bold"), fg=COLORS["text_light"], bg=COLORS["bg_main"]).pack(pady=(10, 10))

        frame_lvl3 = tk.Frame(scrollable_frame, bg=COLORS["bg_main"])
        frame_lvl3.pack()

        kagawads = [f"Kagawad {i}" for i in range(1, 8)]
        # Grid logic: 2 columns or 3 columns
        row = 0
        col = 0
        for pos in kagawads:
            k_frame = tk.Frame(frame_lvl3, bg=COLORS["bg_main"], padx=10, pady=10)
            k_frame.grid(row=row, column=col)
            draw_card(k_frame, pos.upper(), off_map.get(pos, ""), width=220).pack()

            col += 1
            if col > 2:  # 3 items per row
                col = 0
                row += 1

        # -- LEVEL 4: SK CHAIRPERSON --
        tk.Label(scrollable_frame, text=" ", bg=COLORS["bg_main"], font=("Arial", 14), fg="#AAA").pack(pady=5)
        frame_lvl4 = tk.Frame(scrollable_frame, bg=COLORS["bg_main"], pady=20)
        frame_lvl4.pack()
        sk_card = draw_card(frame_lvl4, "SK CHAIRPERSON", off_map.get("SK Chairperson", ""),
                            bg_color="#FFF4E5", fg_title="#FF9800", width=350)
        sk_card.pack()

        # Padding at bottom
        tk.Frame(scrollable_frame, bg=COLORS["bg_main"], height=50).pack()

    # =========================================================
    # EDIT MODE (Form linked to Residents)
    # =========================================================
    def show_edit_mode(self):
        # 1. Fetch latest data
        try:
            res = requests.get(f"{self.api_base}/officials")
            res.raise_for_status()
            self.officials_data = res.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data before editing: {e}")
            return

        # 2. Load Residents for linking
        self.load_residents()

        # Clear container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Header
        header = tk.Frame(self.main_container, bg=COLORS["bg_main"], pady=10, padx=10)
        header.pack(fill="x")
        tk.Label(header, text="Edit Officials", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg_main"], fg=COLORS["text_dark"]).pack(side="left")

        # Form Container (Centered)
        form_outer = tk.Frame(self.main_container, bg=COLORS["bg_main"])
        form_outer.pack(fill="both", expand=True, padx=20, pady=10)

        # Scrollable Form
        canvas = tk.Canvas(form_outer, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_outer, orient="vertical", command=canvas.yview)
        form_frame = tk.Frame(canvas, bg=COLORS["bg_main"])

        form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # -- MOUSEWHEEL --
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        form_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        form_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Map current values
        off_map = {item['position']: item['full_name'] for item in self.officials_data}
        self.entries = {}

        positions_order = [
            "Barangay Captain",
            "Barangay Secretary",
            "Barangay Treasurer",
            "Kagawad 1", "Kagawad 2", "Kagawad 3",
            "Kagawad 4", "Kagawad 5", "Kagawad 6", "Kagawad 7",
            "SK Chairperson"
        ]

        # Generate Fields
        for i, pos in enumerate(positions_order):
            row_frame = tk.Frame(form_frame, bg=COLORS["bg_main"], pady=5)
            row_frame.pack(fill="x")

            tk.Label(row_frame, text=pos + ":", width=20, anchor="e",
                     bg=COLORS["bg_main"], font=("Segoe UI", 10)).pack(side="left", padx=10)

            # --- MODIFIED: USE SEARCHABLE COMBOBOX INSTEAD OF ENTRY ---
            current_val = off_map.get(pos, "")

            cb = ttk.Combobox(row_frame, width=40, font=("Segoe UI", 10))
            cb.pack(side="left", padx=10)

            # Populate with residents
            cb['values'] = self.resident_list

            # Set current value (try to match existing name if possible, else just show name)
            # Heuristic: If current value matches a name in the list, set it.
            if current_val:
                cb.set(current_val)

            # Bind Filter Logic
            cb.bind("<KeyRelease>", self.filter_combobox)

            self.entries[pos] = cb

        # Actions
        btn_frame = tk.Frame(form_frame, bg=COLORS["bg_main"], pady=20)
        btn_frame.pack()

        tk.Button(btn_frame, text="Save Changes", bg=COLORS["secondary"], fg="white",
                  font=("Segoe UI", 10, "bold"), padx=20, pady=5, relief="flat",
                  command=self.save_officials).pack(side="left", padx=10)

        tk.Button(btn_frame, text="Cancel", bg="#E4E6EB", fg=COLORS["text_dark"],
                  font=("Segoe UI", 10), padx=20, pady=5, relief="flat",
                  command=self.show_view_mode).pack(side="left", padx=10)

    # =========================================================
    # FILTER COMBOBOX (Same as Household/Resident Search)
    # =========================================================
    def filter_combobox(self, event):
        widget = event.widget
        if event.keysym in ["Return", "Up", "Down", "Tab", "Left", "Right"]:
            return

        typed = widget.get().lower()
        if not typed:
            widget['values'] = self.resident_list
        else:
            filtered = [r for r in self.resident_list if typed in r.lower()]
            widget['values'] = filtered

    def save_officials(self):
        original_map = {item['position']: item['full_name'] for item in self.officials_data}
        payload = []
        changes_detected = False

        for pos, widget in self.entries.items():
            raw_val = widget.get().strip()

            # --- EXTRACT NAME FROM "ID - NAME" FORMAT ---
            # If user selected from dropdown, it looks like "101 - Juan Cruz"
            # We want to save just "Juan Cruz" to keep the chart clean and compatible.
            if " - " in raw_val and raw_val[0].isdigit():
                # Split only on the first " - " occurrence
                final_val = raw_val.split(" - ", 1)[1]
            else:
                # User typed a name manually or didn't select from list
                final_val = raw_val

            old_val = original_map.get(pos, "")

            if final_val != old_val:
                payload.append({
                    "position": pos,
                    "full_name": final_val
                })
                changes_detected = True

        if not changes_detected:
            messagebox.showinfo("Info", "No changes detected.")
            self.show_view_mode()
            return

        try:
            res = requests.post(f"{self.api_base}/officials/update", json=payload)
            res.raise_for_status()
            messagebox.showinfo("Success", "Officials updated successfully.")
            # Reload data and switch back to view
            self.load_officials(initial=False)
            self.show_view_mode()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")