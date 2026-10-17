import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime

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

class BlottersTab:
    def __init__(self, parent, api_base, user_session):
        self.parent = parent
        self.api_base = api_base
        self.user_session = user_session
        self.tab = tk.Frame(self.parent, bg=COLORS["bg_main"])
        self.resident_list = []
        self.blotter_map = {}

        # Configure grid weights for the main tab
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(0, weight=1)

        self.build_tab()

    def build_tab(self):
        # ===================== MAIN NOTEBOOK (TABS) =====================
        self.main_notebook = ttk.Notebook(self.tab)
        self.main_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # === TAB 1: BLOTTER RECORDS
        self.list_tab = tk.Frame(self.main_notebook, bg=COLORS["bg_main"])
        self.main_notebook.add(self.list_tab, text=" Blotter Records ")

        # === TAB 2: ENTRY FORM
        self.form_tab = tk.Frame(self.main_notebook, bg=COLORS["bg_main"])
        self.main_notebook.add(self.form_tab, text=" Case Entry Form ")

        # =================================================================
        # BUILD TAB 1: LIST VIEW
        # =================================================================

        # 1. SEARCH BAR CARD
        search_card = tk.Frame(self.list_tab, bg=COLORS["bg_card"], bd=1, relief="solid")
        search_card.pack(fill="x", padx=10, pady=10)

        search_inner = tk.Frame(search_card, bg=COLORS["bg_card"], padx=10, pady=10)
        search_inner.pack(fill="x")

        tk.Label(search_inner, text="Search Case:", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["text_dark"]).pack(side="left", padx=(0, 10))

        self.search_entry = tk.Entry(search_inner, width=40, font=("Segoe UI", 10), bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=5, ipady=3)
        self.search_entry.bind("<Return>", lambda e: self.search_blotters())

        tk.Button(search_inner, text="Search", bg=COLORS["primary"], fg="white",
                  font=("Segoe UI", 9), relief="flat", padx=10, command=self.search_blotters).pack(side="left", padx=5)

        tk.Button(search_inner, text="Clear", bg=COLORS["bg_main"], fg=COLORS["text_dark"],
                  font=("Segoe UI", 9), relief="flat", padx=10, command=self.clear_search).pack(side="left", padx=5)

        # 2. TABLE AREA
        table_container = tk.Frame(self.list_tab, bg=COLORS["bg_main"])
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("id", "nature", "complainant", "defendant", "status", "remarks")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.column("id", anchor="center", width=50)

        self.tree.heading("nature", text="Nature of Case")
        self.tree.column("nature", anchor="w", width=150)

        self.tree.heading("complainant", text="Complainant")
        self.tree.column("complainant", anchor="w", width=150)

        self.tree.heading("defendant", text="Defendant")
        self.tree.column("defendant", anchor="w", width=150)

        self.tree.heading("status", text="Status")
        self.tree.column("status", anchor="center", width=100)

        self.tree.heading("remarks", text="Remarks")
        self.tree.column("remarks", anchor="w", width=200)

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Bindings
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Button-3>", self.show_blotter_statements)
        self.tree.bind("<Double-1>", lambda e: self.main_notebook.select(self.form_tab))

        # 3. LIST ACTION BUTTONS
        list_btn_frame = tk.Frame(self.list_tab, bg=COLORS["bg_main"], pady=5)
        list_btn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(list_btn_frame, text="Create New Case", bg=COLORS["secondary"], fg="white",
                  font=("Segoe UI", 10, "bold"), padx=15, pady=5,
                  command=lambda: [self.clear_form(), self.main_notebook.select(self.form_tab)]).pack(side="left")

        tk.Button(list_btn_frame, text="Edit Selected Details", bg=COLORS["primary"], fg="white",
                  font=("Segoe UI", 10), padx=15, pady=5,
                  command=lambda: self.main_notebook.select(self.form_tab)).pack(side="left", padx=10)

        # View Incidents Button
        tk.Button(list_btn_frame, text="View Incidents", bg=COLORS["primary"], fg="white",
                  font=("Segoe UI", 10), padx=15, pady=5,
                  command=self.view_statement_button).pack(side="left", padx=5)

        if self.user_session.get("role") == "Admin":
            tk.Button(list_btn_frame, text="Delete Selected", bg=COLORS["danger"], fg="white",
                      font=("Segoe UI", 10), padx=15, pady=5, command=self.do_delete).pack(side="right")


        # =================================================================
        # BUILD TAB 2: FORM VIEW (SCROLLABLE)
        # =================================================================

        btn_frame = tk.Frame(self.form_tab, bg=COLORS["bg_card"], pady=15, padx=10, bd=1, relief="raised")
        btn_frame.pack(side="bottom", fill="x")

        tk.Button(btn_frame, text="Save / Update Case", width=20, bg=COLORS["secondary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=5, command=self.do_add).pack(side="left", padx=10)

        tk.Button(btn_frame, text="View Incidents", width=18, bg=COLORS["primary"], fg="white",
                  font=("Segoe UI", 10), relief="flat", pady=5, command=self.view_statement_button).pack(side="left",
                                                                                                         padx=5)

        tk.Button(btn_frame, text="Clear Fields", width=15, bg="#E4E6EB", fg=COLORS["text_dark"],
                  font=("Segoe UI", 10), relief="flat", pady=5, command=self.clear_form).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Back to List", width=15, bg=COLORS["bg_main"], fg=COLORS["text_dark"],
                  font=("Segoe UI", 10), relief="flat", pady=5,
                  command=lambda: self.main_notebook.select(self.list_tab)).pack(side="right", padx=10)

        # 2. SCROLLABLE CANVAS AREA
        canvas_container = tk.Frame(self.form_tab, bg=COLORS["bg_main"])
        canvas_container.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_container, bg=COLORS["bg_main"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)

        self.scrollable_form_frame = tk.Frame(self.canvas, bg=COLORS["bg_main"], padx=10, pady=10)
        self.scrollable_form_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_form_frame, anchor="nw")

        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas.bind("<Configure>", on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- Mousewheel Scrolling Logic ---
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        self.scrollable_form_frame.bind("<Enter>", _bind_mousewheel)
        self.scrollable_form_frame.bind("<Leave>", _unbind_mousewheel)

        # 3. ADD WIDGETS TO SCROLLABLE FRAME

        # --- A. General Info Card ---
        gen_card = tk.LabelFrame(self.scrollable_form_frame, text="Case Information", bg=COLORS["bg_card"],
                                 fg=COLORS["text_light"], font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        gen_card.pack(fill="x", pady=(0, 10))

        gen_card.columnconfigure(1, weight=1)
        gen_card.columnconfigure(3, weight=1)
        gen_card.columnconfigure(5, weight=1)

        # Row 0
        tk.Label(gen_card, text="Date:", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="w")
        self.e_date = tk.Entry(gen_card, width=15)
        self.e_date.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.e_date.insert(0, datetime.today().strftime("%Y-%m-%d"))

        tk.Label(gen_card, text="Nature:", bg=COLORS["bg_card"]).grid(row=0, column=2, sticky="w")
        self.e_nature = ttk.Combobox(gen_card, values=[
            "Physical Injury", "Theft", "Gossip/Oral Defamation", "Property Damage",
            "Collection of Debt", "Unjust Vexation", "Others"
        ], state="readonly")
        self.e_nature.grid(row=0, column=3, sticky="ew", padx=5)

        tk.Label(gen_card, text="Status:", bg=COLORS["bg_card"]).grid(row=0, column=4, sticky="w")
        self.e_status = ttk.Combobox(gen_card,
                                     values=["Active", "Settled", "Dismissed", "Pending Hearing", "Endorsed to Court"],
                                     state="readonly")
        self.e_status.set("Active")
        self.e_status.grid(row=0, column=5, sticky="ew", padx=5)

        # Row 1
        tk.Label(gen_card, text="Remarks:", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="w", pady=5)
        self.e_remarks = tk.Entry(gen_card)
        self.e_remarks.grid(row=1, column=1, columnspan=5, sticky="ew", padx=5, pady=5)

        # --- B. Parties Card (Side by Side) ---
        parties_frame = tk.Frame(self.scrollable_form_frame, bg=COLORS["bg_main"])
        parties_frame.pack(fill="x", pady=(0, 10))
        parties_frame.columnconfigure(0, weight=1)
        parties_frame.columnconfigure(1, weight=1)

        # Left: Complainant
        self.c_frame = tk.LabelFrame(parties_frame, text="Complainant", bg=COLORS["bg_card"],
                                     fg=COLORS["primary"], font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        self.c_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.c_frame.columnconfigure(1, weight=1)

        tk.Label(self.c_frame, text="Type:", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="w")
        self.comp_type = ttk.Combobox(self.c_frame, values=["Resident", "Non-resident"], state="readonly", width=12)
        self.comp_type.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.comp_type.set("Resident")
        self.comp_type.bind("<<ComboboxSelected>>", self.switch_complainant_type)

        tk.Label(self.c_frame, text="Name:", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.complainant_combo = ttk.Combobox(self.c_frame)
        self.complainant_combo.bind("<KeyRelease>", self.filter_complainant)
        self.complainant_combo.bind("<FocusIn>", lambda e: self.reload_residents())
        self.complainant_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.complainant_entry = tk.Entry(self.c_frame)  # Hidden initially

        self.lbl_c_addr = tk.Label(self.c_frame, text="Address:", bg=COLORS["bg_card"])
        self.ent_c_addr = tk.Entry(self.c_frame)
        self.lbl_c_cont = tk.Label(self.c_frame, text="Contact:", bg=COLORS["bg_card"])
        self.ent_c_cont = tk.Entry(self.c_frame)

        # Right: Defendant
        self.d_frame = tk.LabelFrame(parties_frame, text="Defendant", bg=COLORS["bg_card"],
                                     fg=COLORS["danger"], font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        self.d_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.d_frame.columnconfigure(1, weight=1)

        tk.Label(self.d_frame, text="Type:", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="w")
        self.def_type = ttk.Combobox(self.d_frame, values=["Resident", "Non-resident"], state="readonly", width=12)
        self.def_type.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.def_type.set("Resident")
        self.def_type.bind("<<ComboboxSelected>>", self.switch_defendant_type)

        tk.Label(self.d_frame, text="Name:", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.defendant_combo = ttk.Combobox(self.d_frame)
        self.defendant_combo.bind("<KeyRelease>", self.filter_defendant)
        self.defendant_combo.bind("<FocusIn>", lambda e: self.reload_residents())
        self.defendant_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))

        self.defendant_entry = tk.Entry(self.d_frame)  # Hidden initially

        self.lbl_d_addr = tk.Label(self.d_frame, text="Address:", bg=COLORS["bg_card"])
        self.ent_d_addr = tk.Entry(self.d_frame)
        self.lbl_d_cont = tk.Label(self.d_frame, text="Contact:", bg=COLORS["bg_card"])
        self.ent_d_cont = tk.Entry(self.d_frame)

        # --- C. Narrative & Statements ---
        narrative_frame = tk.Frame(self.scrollable_form_frame, bg=COLORS["bg_main"])
        narrative_frame.pack(fill="both", expand=True)
        narrative_frame.columnconfigure(0, weight=1)
        narrative_frame.columnconfigure(1, weight=1)

        tk.Label(narrative_frame, text="Incident Details:", bg=COLORS["bg_main"], font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=(5, 0))
        self.e_details = tk.Text(narrative_frame, height=4, width=50, font=("Segoe UI", 10))
        self.e_details.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        tk.Label(narrative_frame, text="Complainant Statement:", bg=COLORS["bg_main"],
                 font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        self.comp_statement = tk.Text(narrative_frame, height=4, width=30, font=("Segoe UI", 10))
        self.comp_statement.grid(row=3, column=0, sticky="nsew", padx=(0, 5), pady=2)

        tk.Label(narrative_frame, text="Defendant Statement:", bg=COLORS["bg_main"], font=("Segoe UI", 9, "bold")).grid(
            row=2, column=1, sticky="w")
        self.def_statement = tk.Text(narrative_frame, height=4, width=30, font=("Segoe UI", 10))
        self.def_statement.grid(row=3, column=1, sticky="nsew", padx=(5, 0), pady=2)

        self.reload_residents()
        self.load_blotters()

    # ================= SEARCH =================
    def search_blotters(self):
        q = self.search_entry.get().strip().lower()
        if not q:
            self.load_blotters()
            return

        if not self.blotter_map:
            self.load_blotters()

        self.tree.delete(*self.tree.get_children())

        for b in self.blotter_map.values():
            # Convert fields to string and lower case for comparison
            b_id = str(b.get("id", "")).lower()
            comp = str(b.get("complainant_name", "")).lower()
            defe = str(b.get("defendant_name", "")).lower()
            nature = str(b.get("nature_of_case", "")).lower()
            status = str(b.get("status", "")).lower()
            remarks = str(b.get("remarks", "")).lower()

            # Check if query exists in ANY of these fields
            if (q in b_id or
                    q in comp or
                    q in defe or
                    q in nature or
                    q in status or
                    q in remarks):
                self.tree.insert("", "end", values=(
                    b["id"],
                    b.get("nature_of_case", ""),
                    b["complainant_name"],
                    b["defendant_name"],
                    b.get("status", "Active"),
                    b.get("remarks", "")
                ))

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.load_blotters()

    # ===================== CHECK EXISTING CASE =====================
    def check_existing_case(self, complainant, defendant):
        for b in self.blotter_map.values():
            if (b.get("complainant_name") == complainant and
                    b.get("defendant_name") == defendant):
                return b
        return None

    # ===================== ADD / APPEND INCIDENT =====================
    def do_add(self):
        # 1. VALIDATE & COLLECT INPUTS
        comp_addr = ""
        comp_cont = ""

        # Complainant
        if self.comp_type.get() == "Resident":
            raw_comp = self.complainant_combo.get()
            if " - " in raw_comp:
                comp = raw_comp.split(" - ", 1)[1]
            else:
                comp = raw_comp
        else:
            comp = self.complainant_entry.get().strip()
            comp_addr = self.ent_c_addr.get().strip()
            comp_cont = self.ent_c_cont.get().strip()
            if comp_cont and (not comp_cont.isdigit() or len(comp_cont) != 11):
                messagebox.showwarning("Validation", "Complainant Contact must be 11 digits.")
                return

        # Defendant
        def_addr = ""
        def_cont = ""
        if self.def_type.get() == "Resident":
            raw_defe = self.defendant_combo.get()
            if " - " in raw_defe:
                defe = raw_defe.split(" - ", 1)[1]
            else:
                defe = raw_defe
        else:
            defe = self.defendant_entry.get().strip()
            def_addr = self.ent_d_addr.get().strip()
            def_cont = self.ent_d_cont.get().strip()
            if def_cont and (not def_cont.isdigit() or len(def_cont) != 11):
                messagebox.showwarning("Validation", "Defendant Contact must be 11 digits.")
                return

        if not comp or not defe:
            messagebox.showwarning("Missing", "Complainant and defendant required.")
            return

        if comp == defe:
            messagebox.showwarning("Error", "Complainant & Defendant cannot be the same.")
            return

        # Common Data
        nature = self.e_nature.get().strip()
        status = self.e_status.get().strip()
        remarks = self.e_remarks.get().strip()
        incident_date = self.e_date.get().strip()
        details = self.e_details.get("1.0", "end").strip()
        comp_stmt = self.comp_statement.get("1.0", "end").strip()
        def_stmt = self.def_statement.get("1.0", "end").strip()

        # --- CHECK EXISTING BLOTTER ---
        existing = self.check_existing_case(comp, defe)
        if existing:
            # Found duplicate names -> Ask user what to do
            answer = messagebox.askyesno(
                "Existing Blotter Found",
                "This complainant and defendant already have a blotter.\n\n"
                "Is this the SAME INCIDENT (Append to History)?\n"
                "Click NO to create a separate case file."
            )

            if answer:
                # SAME INCIDENT -> append
                payload = {
                    "complainant_name": comp,
                    "defendant_name": defe,
                    "incident_date": incident_date,
                    "details": details,
                    "complainant_statement": comp_stmt,
                    "defendant_statement": def_stmt,
                    "same_incident": True,
                    "nature_of_case": nature,  # Update nature just in case
                    "status": status,
                    "remarks": remarks
                }
                self.send_blotter_data(payload, "Updated", "Details appended to existing incident.")
                return
            else:
                # DIFFERENT INCIDENT -> Ask confirmation
                ask = messagebox.askyesno("New Incident", "Do you want to ADD this as a NEW INCIDENT record?")
                if not ask: return

                payload = {
                    "complainant_name": comp,
                    "defendant_name": defe,
                    "incident_date": incident_date,
                    "details": details,
                    "complainant_statement": comp_stmt,
                    "defendant_statement": def_stmt,
                    "same_incident": False,
                    "nature_of_case": nature,
                    "status": status,
                    "remarks": remarks
                }
                self.send_blotter_data(payload, "Added", "New incident added.")
                return

        # NEW BLOTTER (No existing found)
        payload = {
            "complainant_name": comp,
            "defendant_name": defe,
            "complainant_address": comp_addr,
            "complainant_contact": comp_cont,
            "defendant_address": def_addr,
            "defendant_contact": def_cont,
            "incident_date": incident_date,
            "details": details,
            "complainant_statement": comp_stmt,
            "defendant_statement": def_stmt,
            "same_incident": None,
            "nature_of_case": nature,
            "status": status,
            "remarks": remarks
        }
        self.send_blotter_data(payload, "Created", "New blotter created.")

    def send_blotter_data(self, payload, success_title, success_msg):
        try:
            res = requests.post(f"{self.api_base}/blotter", json=payload)
            res.raise_for_status()
            messagebox.showinfo(success_title, success_msg)
            self.load_blotters()
            self.clear_form()
        except Exception as e:
            msg = f"Failed to save:\n{e}"
            if 'res' in locals() and hasattr(res, 'text'):
                msg += f"\nServer: {res.text}"
            messagebox.showerror("Error", msg)

    # ===================== VIEW STATEMENTS =====================
    def view_statement_button(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a blotter to view.")
            return

        blotter_id = int(self.tree.item(sel[0], "values")[0])
        self.fetch_and_show_incidents(blotter_id)

    def show_blotter_statements(self, event):
        row = self.tree.identify_row(event.y)
        if not row: return
        blotter_id = int(self.tree.item(row, "values")[0])
        self.fetch_and_show_incidents(blotter_id)

    def fetch_and_show_incidents(self, blotter_id):
        try:
            r = requests.get(f"{self.api_base}/blotter/{blotter_id}/incidents")
            r.raise_for_status()
            data = r.json()
            self.open_incident_history_window(data, blotter_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load incidents: {e}")

    # ===================== INCIDENT HISTORY WINDOW =====================
    def open_incident_history_window(self, data, blotter_id):
        if isinstance(data, dict):
            blotter = data.get("blotter", {})
            incidents = data.get("incidents", [])
        else:
            blotter = {}
            incidents = data

        win = tk.Toplevel(self.parent)
        win.title(f"Incident History - Blotter #{blotter_id}")
        win.geometry("900x700")

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True)

        incident_number = 0
        grouped = []
        current = None

        for inc in incidents:
            speaker = inc.get("speaker")
            if speaker == "both":
                incident_number += 1
                current = {
                    "incident_no": incident_number,
                    "date": inc.get("incident_date"),
                    "details": inc.get("details", "").strip(),
                    "comp": [],
                    "def": [],
                }
                grouped.append(current)
            elif speaker == "complainant" and current:
                current["comp"].append(inc.get("statement", "").strip())
            elif speaker == "defendant" and current:
                current["def"].append(inc.get("statement", "").strip())

        for g in grouped:
            tab = tk.Frame(notebook)
            notebook.add(tab, text=f"Incident #{g['incident_no']}")

            container = tk.Frame(tab)
            container.pack(fill="both", expand=True, padx=10, pady=10)

            text = tk.Text(container, wrap="word", font=("Courier New", 10))
            text.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(container, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.configure(yscrollcommand=scrollbar.set)

            report = []
            report.append("====================================================")
            report.append(f"                 INCIDENT #{g['incident_no']}")
            report.append("----------------------------------------------------")
            report.append(f"Date of Incident: {g['date']}")
            report.append(f"Status: {blotter.get('status')} | Case: {blotter.get('nature_of_case')}")
            report.append("====================================================\n")

            report.append("DETAILS:")
            report.append(f"{g['details']}\n")
            report.append("----------------------------------------------------")

            c_name = blotter.get("complainant_name", "N/A")
            c_addr = blotter.get("complainant_address") or "(Resident/Not Recorded)"
            c_cont = blotter.get("complainant_contact") or "N/A"

            report.append("COMPLAINANT INFORMATION:")
            report.append(f"Name:    {c_name}")
            report.append(f"Address: {c_addr}")
            report.append(f"Contact: {c_cont}")
            report.append("\nCOMPLAINANT STATEMENTS:")
            if g["comp"]:
                for s in g["comp"]: report.append(f"- {s}")
            else:
                report.append("(none)")

            report.append("\n----------------------------------------------------")

            d_name = blotter.get("defendant_name", "N/A")
            d_addr = blotter.get("defendant_address") or "(Resident/Not Recorded)"
            d_cont = blotter.get("defendant_contact") or "N/A"

            report.append("DEFENDANT INFORMATION:")
            report.append(f"Name:    {d_name}")
            report.append(f"Address: {d_addr}")
            report.append(f"Contact: {d_cont}")
            report.append("\nDEFENDANT STATEMENTS:")
            if g["def"]:
                for s in g["def"]: report.append(f"- {s}")
            else:
                report.append("(none)")

            text.insert("end", "\n".join(report))
            text.configure(state="disabled")

        tk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    # ===================== LOAD BLOTTERS =====================
    def load_blotters(self):
        self.tree.delete(*self.tree.get_children())
        self.blotter_map = {}
        try:
            res = requests.get(f"{self.api_base}/blotters")
            res.raise_for_status()
            data = res.json()
            for b in data:
                blotter_id = b["id"]
                self.blotter_map[blotter_id] = b
                self.tree.insert("", "end", values=(
                    blotter_id,
                    b.get("nature_of_case", ""),
                    b.get("complainant_name"),
                    b.get("defendant_name"),
                    b.get("status", "Active"),
                    b.get("remarks", "")
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load blotters:\n{e}")

    # ===================== FILL FORM WHEN SELECTING ROW =====================
    def on_tree_select(self, e):
        selection = self.tree.selection()
        if not selection: return

        blotter_id = int(self.tree.item(selection[0], "values")[0])
        blotter = self.blotter_map.get(blotter_id)
        if not blotter: return

        # 1. Fill Basic Fields from the Treeview/Map data
        comp_name = blotter.get("complainant_name", "")
        defe_name = blotter.get("defendant_name", "")

        self.e_date.delete(0, tk.END)
        self.e_date.insert(0, blotter.get("last_incident", ""))

        self.e_nature.set(blotter.get("nature_of_case", ""))
        self.e_status.set(blotter.get("status", "Active"))
        self.e_remarks.delete(0, tk.END)
        if blotter.get("remarks"):
            self.e_remarks.insert(0, blotter.get("remarks"))

        # 2. Fill Text Areas (Details & Statements) by fetching from Server
        self.e_details.delete("1.0", tk.END)
        self.comp_statement.delete("1.0", tk.END)
        self.def_statement.delete("1.0", tk.END)

        try:
            # Fetch all incidents for this blotter
            res = requests.get(f"{self.api_base}/blotter/{blotter_id}/incidents")
            if res.status_code == 200:
                data = res.json()
                incidents = data.get("incidents", [])
                latest_details = ""
                latest_comp_stmt = ""
                latest_def_stmt = ""

                for inc in reversed(incidents):
                    speaker = inc.get("speaker", "")
                    content = inc.get("details") or inc.get("statement") or ""

                    if speaker == "both" and not latest_details:
                        latest_details = content
                    elif speaker == "complainant" and not latest_comp_stmt:
                        latest_comp_stmt = content
                    elif speaker == "defendant" and not latest_def_stmt:
                        latest_def_stmt = content

                if latest_details: self.e_details.insert("1.0", latest_details)
                if latest_comp_stmt: self.comp_statement.insert("1.0", latest_comp_stmt)
                if latest_def_stmt: self.def_statement.insert("1.0", latest_def_stmt)

        except Exception as err:
            print(f"Failed to fetch incident details: {err}")

        # 3. Match Resident Complainant (Existing Logic)
        if any(comp_name in s for s in self.resident_list):
            self.comp_type.set("Resident")
            self.switch_complainant_type()
            match = next((s for s in self.resident_list if comp_name in s), comp_name)
            self.complainant_combo.set(match)
        else:
            self.comp_type.set("Non-resident")
            self.switch_complainant_type()
            self.complainant_entry.delete(0, tk.END)
            self.complainant_entry.insert(0, comp_name)
            self.ent_c_addr.delete(0, tk.END)
            if blotter.get("complainant_address"):
                self.ent_c_addr.insert(0, blotter.get("complainant_address"))
            self.ent_c_cont.delete(0, tk.END)
            if blotter.get("complainant_contact"):
                self.ent_c_cont.insert(0, blotter.get("complainant_contact"))

        # 4. Match Resident Defendant (Existing Logic)
        if any(defe_name in s for s in self.resident_list):
            self.def_type.set("Resident")
            self.switch_defendant_type()
            match = next((s for s in self.resident_list if defe_name in s), defe_name)
            self.defendant_combo.set(match)
        else:
            self.def_type.set("Non-resident")
            self.switch_defendant_type()
            self.defendant_entry.delete(0, tk.END)
            self.defendant_entry.insert(0, defe_name)
            # Fill address/contact
            self.ent_d_addr.delete(0, tk.END)
            if blotter.get("defendant_address"):
                self.ent_d_addr.insert(0, blotter.get("defendant_address"))
            self.ent_d_cont.delete(0, tk.END)
            if blotter.get("defendant_contact"):
                self.ent_d_cont.insert(0, blotter.get("defendant_contact"))

    # ===================== DELETE =====================
    def do_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a blotter to delete.")
            return

        blotter_id = int(self.tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Confirm", "Delete this blotter and ALL its incidents?"):
            return

        try:
            res = requests.delete(f"{self.api_base}/blotter/{blotter_id}")
            res.raise_for_status()
            messagebox.showinfo("Deleted", "Blotter deleted.")
            self.load_blotters()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed:\n{e}")

    # ===================== RESIDENT LOADING =====================
    def reload_residents(self):
        try:
            res = requests.get(f"{self.api_base}/residents")
            res.raise_for_status()
            data = res.json()

            self.resident_map = {}
            self.resident_list = []
            for r in data:
                ext = r.get("extension", "")
                if ext and ext != "N/A":
                    full = f"{r['id']} - {r['first_name']} {r['last_name']} {ext}"
                else:
                    full = f"{r['id']} - {r['first_name']} {r['last_name']}"

                self.resident_map[full] = r["id"]
                self.resident_list.append(full)

            if self.comp_type.get() == "Resident":
                self.complainant_combo["values"] = self.resident_list
            if self.def_type.get() == "Resident":
                self.defendant_combo["values"] = self.resident_list
        except:
            self.resident_map = {}
            self.resident_list = []

    # ===================== FILTERING NAME =====================
    def filter_complainant(self, e):
        typed = self.complainant_combo.get().lower()
        filtered = [name for name in self.resident_list if typed in name.lower()]
        self.complainant_combo["values"] = filtered

    def filter_defendant(self, e):
        typed = self.defendant_combo.get().lower()
        filtered = [name for name in self.resident_list if typed in name.lower()]
        comp = self.complainant_combo.get()
        filtered = [n for n in filtered if n != comp]
        self.defendant_combo["values"] = filtered

    # ===================== SWITCH RESIDENT/NONRESIDENT =====================
    def switch_complainant_type(self, e=None):
        if self.comp_type.get() == "Resident":
            self.complainant_entry.grid_remove()
            self.lbl_c_addr.grid_remove()
            self.ent_c_addr.grid_remove()
            self.lbl_c_cont.grid_remove()
            self.ent_c_cont.grid_remove()
            self.complainant_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))
        else:
            self.complainant_combo.grid_remove()
            self.complainant_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))
            self.lbl_c_addr.grid(row=2, column=0, sticky="w", pady=5)
            self.ent_c_addr.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            self.lbl_c_cont.grid(row=3, column=0, sticky="w", pady=5)
            self.ent_c_cont.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

    def switch_defendant_type(self, e=None):
        if self.def_type.get() == "Resident":
            self.defendant_entry.grid_remove()
            self.lbl_d_addr.grid_remove()
            self.ent_d_addr.grid_remove()
            self.lbl_d_cont.grid_remove()
            self.ent_d_cont.grid_remove()
            self.defendant_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))
        else:
            self.defendant_combo.grid_remove()
            self.defendant_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))
            self.lbl_d_addr.grid(row=2, column=0, sticky="w", pady=5)
            self.ent_d_addr.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            self.lbl_d_cont.grid(row=3, column=0, sticky="w", pady=5)
            self.ent_d_cont.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

    # ===================== CLEAR FORM =====================
    def clear_form(self):
        self.complainant_combo.set("")
        self.complainant_entry.delete(0, tk.END)
        self.ent_c_addr.delete(0, tk.END)
        self.ent_c_cont.delete(0, tk.END)
        self.comp_statement.delete("1.0", tk.END)

        self.defendant_combo.set("")
        self.defendant_entry.delete(0, tk.END)
        self.ent_d_addr.delete(0, tk.END)
        self.ent_d_cont.delete(0, tk.END)
        self.def_statement.delete("1.0", tk.END)

        self.e_date.delete(0, tk.END)
        self.e_date.insert(0, datetime.today().strftime("%Y-%m-%d"))

        self.e_details.delete("1.0", tk.END)
        self.e_nature.set("")
        self.e_status.set("Active")
        self.e_remarks.delete(0, tk.END)