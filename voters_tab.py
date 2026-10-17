import tkinter as tk
from tkinter import ttk, messagebox
import requests


class VotersTab:
    def __init__(self, parent, api_base):
        self.parent = parent
        self.api_base = api_base
        self.tab = tk.Frame(self.parent)
        self.build_tab()

    def build_tab(self):
        # TOP BAR / FILTER
        top = tk.Frame(self.tab)
        top.pack(fill="x", padx=8, pady=6)

        # Title
        tk.Label(top, text="Voter's List", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)

        # --- Search / Filter frame on the right ---
        search_frame = tk.Frame(top)
        search_frame.pack(side="right")

        # 1. Status Filter (NEW)
        tk.Label(search_frame, text="Status:").grid(row=0, column=0, padx=3)
        self.status_combo = ttk.Combobox(
            search_frame,
            values=["Voter", "Non-voter", "All"],
            state="readonly",
            width=10
        )
        self.status_combo.set("Voter")  # Default
        self.status_combo.grid(row=0, column=1, padx=3)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.load_voters())

        # 2. Purok Filter
        tk.Label(search_frame, text="Purok:").grid(row=0, column=2, padx=3)
        self.purok_combo = ttk.Combobox(
            search_frame,
            values=["All", "Purok 1", "Purok 2", "Purok 3", "Purok 4", "Purok 5", "Purok 6", "Purok 7"],
            state="readonly",
            width=12
        )
        self.purok_combo.set("All")
        self.purok_combo.grid(row=0, column=3, padx=3)

        # 3. Name Search
        tk.Label(search_frame, text="Search Name:").grid(row=0, column=4, padx=6)
        self.search_entry = tk.Entry(search_frame, width=25)
        self.search_entry.grid(row=0, column=5, padx=3)
        self.search_entry.bind("<Return>", lambda e: self.load_voters())

        # BUTTONS (Go and Clear)
        tk.Button(search_frame, text="Go", width=6, command=self.load_voters).grid(row=0, column=6, padx=3)
        tk.Button(search_frame, text="Clear", width=6, command=self.clear_search).grid(row=0, column=7, padx=3)

        # TABLE FRAME
        table_frame = tk.Frame(self.tab)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        columns = ("purok", "full_name", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # HEADERS
        self.tree.heading("purok", text="Purok", anchor="center")
        self.tree.heading("full_name", text="Resident Name", anchor="w")
        self.tree.heading("status", text="Status", anchor="center")

        # COLUMNS
        self.tree.column("purok", width=100, anchor="center")
        self.tree.column("full_name", width=500, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        # SCROLLBAR
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # TOTAL LABEL
        self.total_label = tk.Label(self.tab, text="Total Records: 0", font=("Segoe UI", 10, "bold"))
        self.total_label.pack(anchor="e", padx=8, pady=4)

        # INITIAL LOAD
        self.load_voters()

    def load_voters(self):
        purok = self.purok_combo.get()
        status = self.status_combo.get()
        q = self.search_entry.get().strip()

        params = {}
        if purok: params["purok"] = purok
        if status: params["status"] = status
        if q: params["q"] = q

        try:
            url = f"{self.api_base}/voters"
            res = requests.get(url, params=params, timeout=6)
            res.raise_for_status()
            voters = res.json()

            if not isinstance(voters, list):
                messagebox.showerror("Error", "Unexpected response format from server")
                return

            self.tree.delete(*self.tree.get_children())

            for v in voters:
                parts = [
                    str(v.get("first_name", "")).strip(),
                    str(v.get("middle_name", "")).strip(),
                    str(v.get("last_name", "")).strip(),
                    str(v.get("extension", "")).strip()
                ]
                full_name = " ".join([p for p in parts if p and p != "N/A" and p != "None"])

                purok_val = v.get("purok", "")
                status_val = v.get("voter_status", "Non-voter")

                tags = ()
                if status_val == "Voter":
                    tags = ('voter',)

                self.tree.insert("", "end", values=(purok_val, full_name, status_val), tags=tags)

            # Update total count
            self.total_label.config(text=f"Total Records: {len(voters)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load list:\n{e}")

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.purok_combo.set("All")
        self.status_combo.set("Voter")
        self.load_voters()