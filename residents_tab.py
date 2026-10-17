import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
import re  # <--- REQUIRED FOR STRICT SEARCH


class ResidentsTab:
    def __init__(self, parent, api_base, user_session):
        self.parent = parent
        self.api_base = api_base
        self.user_session = user_session
        self.tab = tk.Frame(self.parent)

        # Cache for client-side filtering
        self.all_residents_data = []

        self.build_tab()

    def build_tab(self):
        # === Search / Title Row ===
        top = tk.Frame(self.tab)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Residents", font=("Segoe UI", 14, "bold")).pack(side="left")

        search_frame = tk.Frame(top)
        search_frame.pack(side="right")

        tk.Label(search_frame, text="Search:").pack(side="left")
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=4)

        # CHANGED: Bind to KeyRelease for instant filtering
        self.search_entry.bind("<KeyRelease>", self.apply_filter)

        tk.Button(
            search_frame,
            text="Go",
            command=self.apply_filter,
        ).pack(side="left", padx=4)

        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(
            side="left"
        )

        # === Form Frame (balanced grid) ===
        form = tk.LabelFrame(self.tab, text="Resident Information", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=(0, 8))

        # Configure columns
        for i in range(6):
            form.grid_columnconfigure(i, weight=1, uniform="col")

        # Row 0
        tk.Label(form, text="First Name *").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.e_first = tk.Entry(form)
        self.e_first.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Middle Name *").grid(row=0, column=2, sticky="w", padx=4, pady=2)
        self.e_middle = tk.Entry(form)
        self.e_middle.grid(row=0, column=3, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Last Name *").grid(row=0, column=4, sticky="w", padx=4, pady=2)
        self.e_last = tk.Entry(form)
        self.e_last.grid(row=0, column=5, sticky="ew", padx=4, pady=2)

        # Row 1
        tk.Label(form, text="Extension").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        extension_options = ["N/A", "Jr.", "Sr.", "II", "III", "IV", "V"]
        self.e_ext = ttk.Combobox(form, values=extension_options, width=10, state="readonly")
        self.e_ext.set("N/A")
        self.e_ext.grid(row=1, column=1, sticky="w", padx=4, pady=2)

        tk.Label(form, text="Gender *").grid(row=1, column=2, sticky="w", padx=4, pady=2)
        self.e_gender = ttk.Combobox(form, values=["Male", "Female", "Other"], state="readonly")
        self.e_gender.grid(row=1, column=3, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Birthdate (YYYY-MM-DD) *").grid(row=1, column=4, sticky="w", padx=4, pady=2)
        self.e_birth = tk.Entry(form)
        self.e_birth.grid(row=1, column=5, sticky="ew", padx=4, pady=2)

        # Row 2
        tk.Label(form, text="Civil Status *").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        self.e_civil = ttk.Combobox(form, values=["Single", "Married", "Widowed", "Separated", "Divorced"],
                                    state="readonly")
        self.e_civil.grid(row=2, column=1, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Contact *").grid(row=2, column=2, sticky="w", padx=4, pady=2)
        self.e_contact = tk.Entry(form)
        self.e_contact.grid(row=2, column=3, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Occupation *").grid(row=2, column=4, sticky="w", padx=4, pady=2)
        self.e_occupation = tk.Entry(form)
        self.e_occupation.grid(row=2, column=5, sticky="ew", padx=4, pady=2)

        # Row 3
        tk.Label(form, text="Voter Status *").grid(row=3, column=0, sticky="w", padx=4, pady=2)
        self.e_voter = ttk.Combobox(form, values=["Voter", "Non-voter"], state="readonly")
        self.e_voter.grid(row=3, column=1, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Emergency Contact *").grid(row=3, column=2, sticky="w", padx=4, pady=2)
        self.e_emerg = tk.Entry(form)
        self.e_emerg.grid(row=3, column=3, sticky="ew", padx=4, pady=2)

        tk.Label(form, text="Purok *").grid(row=3, column=4, sticky="w", padx=4, pady=2)
        self.e_purok = ttk.Combobox(form, values=[f"Purok {i}" for i in range(1, 8)], state="readonly")
        self.e_purok.grid(row=3, column=5, sticky="ew", padx=4, pady=2)

        # Buttons
        btn_frame = tk.Frame(self.tab)
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))

        tk.Button(btn_frame, text="Add Resident", command=self.do_add).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Update Selected", command=self.do_update).pack(side="left", padx=6)

        if self.user_session.get("role") == "Admin":
            tk.Button(btn_frame, text="Delete Selected", command=self.do_delete, bg="#FF3B30", fg="white").pack(
                side="left", padx=6)

        tk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=6)

        # Table
        table_frame = tk.Frame(self.tab)
        table_frame.pack(fill="both", expand=1, padx=10, pady=6)

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side="bottom", fill="x")

        columns = ("id", "first_name", "middle_name", "last_name", "extension", "gender", "birthdate", "civil_status",
                   "contact", "occupation", "voter_status", "emergency_contact", "purok")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=vsb.set,
                                 xscrollcommand=hsb.set)

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # ADDED SORTING COMMANDS TO HEADINGS
        headers = ["Id", "First Name", "Middle Name", "Last Name", "Ext", "Gender", "Birthdate", "Civil Status",
                   "Contact", "Occupation", "Voter", "Emerg. Contact", "Purok"]

        for col, text in zip(columns, headers):
            self.tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(self.tree, c, False))

            # Set default widths
            if col == "id":
                w = 60
            elif col in ["extension", "purok", "gender"]:
                w = 80
            else:
                w = 120
            self.tree.column(col, width=w, anchor="center" if col in ["id", "purok", "birthdate"] else "w")

        self.tree.pack(fill="both", expand=1, side="left")

        self.total_label = tk.Label(self.tab, text="Total Residents: 0", font=("Segoe UI", 10, "bold"))
        self.total_label.pack(anchor="w", padx=12, pady=(0, 6))

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.load_residents()

    # --------------------------- SORTING FUNCTION ---------------------------
    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    # --------------------------- STRICT FILTER LOGIC ---------------------------
    def apply_filter(self, event=None):
        query = self.search_entry.get().strip()

        if not query:
            self.refresh_tree(self.all_residents_data)
            return

        query_lower = query.lower()
        filtered = []

        # PATTERN MATCHING
        is_id_search = query.isdigit()
        is_date_search = bool(re.match(r'^\d{4}-\d{2}-\d{2}$', query))
        is_purok_search = query_lower.startswith("purok")

        for r in self.all_residents_data:
            # CASE 1: ID SEARCH (Numeric)
            if is_id_search:
                if str(r.get('id', '')) == query:
                    filtered.append(r)

            # CASE 2: BIRTHDAY SEARCH (YYYY-MM-DD)
            elif is_date_search:
                dob = str(r.get('birthdate', ''))
                if dob == query:
                    filtered.append(r)

            # CASE 3: PUROK SEARCH
            elif is_purok_search:
                res_purok = str(r.get('purok', '')).lower()
                if query_lower in res_purok:
                    filtered.append(r)

            # CASE 4: GENERAL TEXT SEARCH (Letters/Names)
            else:
                f = str(r.get('first_name', '')).lower()
                m = str(r.get('middle_name', '')).lower()
                l = str(r.get('last_name', '')).lower()
                e = str(r.get('extension', '')).lower()
                if e == "n/a": e = ""

                full_search_str = f"{f} {m} {l} {e}"

                if query_lower in full_search_str:
                    filtered.append(r)

        self.refresh_tree(filtered)

    def refresh_tree(self, data):
        self.tree.delete(*self.tree.get_children())
        for r in data:
            self.tree.insert(
                "",
                "end",
                values=(
                    r.get("id", ""),
                    r.get("first_name", ""),
                    r.get("middle_name", ""),
                    r.get("last_name", ""),
                    "" if r.get("extension") == "N/A" else r.get("extension", ""),
                    r.get("gender", ""),
                    r.get("birthdate", ""),
                    r.get("civil_status", ""),
                    r.get("contact", ""),
                    r.get("occupation", ""),
                    r.get("voter_status", ""),
                    r.get("emergency_contact", ""),
                    r.get("purok", ""),
                ),
            )

        count = len(data)
        if self.search_entry.get():
            self.total_label.config(text=f"Search Results: {count}")
        else:
            self.total_label.config(text=f"Total Residents: {count}")

    # --------------------------- CRUD ---------------------------
    def load_residents(self, q=None):
        try:
            res = requests.get(f"{self.api_base}/residents", timeout=6)
            res.raise_for_status()
            self.all_residents_data = res.json()
            self.apply_filter()  # Shows all if search box is empty
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load residents:\n{e}")

    # --------------------------- VALIDATION ---------------------------
    def validate_form(self):
        required = [
            ("First Name", self.e_first.get()),
            ("Middle Name", self.e_middle.get()),
            ("Last Name", self.e_last.get()),
            ("Gender", self.e_gender.get()),
            ("Birthdate", self.e_birth.get()),
            ("Civil Status", self.e_civil.get()),
            ("Contact", self.e_contact.get()),
            ("Occupation", self.e_occupation.get()),
            ("Voter Status", self.e_voter.get()),
            ("Emergency Contact", self.e_emerg.get()),
            ("Purok", self.e_purok.get()),
        ]

        for name, val in required:
            if not str(val).strip():
                messagebox.showwarning("Validation", f"{name} is required")
                return False

        try:
            datetime.strptime(self.e_birth.get(), "%Y-%m-%d")
        except Exception:
            messagebox.showwarning("Validation", "Birthdate must be in YYYY-MM-DD format")
            return False

        if not self.e_contact.get().isdigit() or len(self.e_contact.get()) != 11:
            messagebox.showwarning("Validation", "Contact number must be exactly 11 digits")
            return False

        if not self.e_emerg.get().isdigit() or len(self.e_emerg.get()) != 11:
            messagebox.showwarning("Validation", "Emergency contact must be exactly 11 digits")
            return False

        if self.e_contact.get() == self.e_emerg.get():
            messagebox.showwarning("Validation", "Contact and Emergency Contact cannot be the same")
            return False

        return True

    def do_add(self):
        if not self.validate_form():
            return

        first_in = self.e_first.get().strip()
        last_in = self.e_last.get().strip()
        mid_in = self.e_middle.get().strip()
        dob_in = self.e_birth.get().strip()
        contact_in = self.e_contact.get().strip()

        # CLIENT-SIDE DUPLICATE CHECK (Using cached data)
        for c in self.all_residents_data:
            c_first = str(c.get("first_name") or "").strip().lower()
            c_last = str(c.get("last_name") or "").strip().lower()
            c_mid = str(c.get("middle_name") or "").strip().lower()
            c_dob = str(c.get("birthdate") or "").strip()
            c_contact = str(c.get("contact") or "").strip()

            # Check Name + Birthday
            if (c_first == first_in.lower() and
                    c_last == last_in.lower() and
                    c_mid == mid_in.lower() and
                    c_dob == dob_in):

                msg = f"Resident '{first_in} {last_in}' exists. Edit instead?"
                if messagebox.askyesno("Duplicate", msg):
                    self.switch_to_edit(c)
                return

            # Check Contact
            if c_contact == contact_in:
                messagebox.showwarning("Duplicate", f"Contact {contact_in} is already used by {c_first} {c_last}.")
                return

        data = {
            "first_name": first_in,
            "middle_name": mid_in,
            "last_name": last_in,
            "extension": "" if self.e_ext.get() == "N/A" else self.e_ext.get().strip(),
            "gender": self.e_gender.get(),
            "birthdate": dob_in,
            "civil_status": self.e_civil.get(),
            "contact": contact_in,
            "occupation": self.e_occupation.get(),
            "voter_status": self.e_voter.get(),
            "emergency_contact": self.e_emerg.get(),
            "purok": self.e_purok.get(),
        }

        try:
            res = requests.post(f"{self.api_base}/resident", json=data)
            if res.status_code in (200, 201):
                messagebox.showinfo("Success", "Resident added successfully.")
                self.load_residents()
                self.clear_form()
            else:
                messagebox.showerror("Error", f"Failed to add: {res.text}")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server.\n{e}")

    def switch_to_edit(self, resident_data):
        self.search_entry.delete(0, tk.END)
        self.apply_filter()  # Reset filter to show all

        target_id = str(resident_data.get("id"))
        for item_id in self.tree.get_children():
            vals = self.tree.item(item_id, "values")
            if str(vals[0]) == target_id:
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
                self.tree.see(item_id)
                self.on_tree_select(None)
                break

    def do_update(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a resident first")
            return

        if not self.validate_form():
            return

        rid = self.tree.item(sel, "values")[0]
        data = {
            "first_name": self.e_first.get().strip(),
            "middle_name": self.e_middle.get().strip(),
            "last_name": self.e_last.get().strip(),
            "extension": "" if self.e_ext.get() == "N/A" else self.e_ext.get().strip(),
            "gender": self.e_gender.get(),
            "birthdate": self.e_birth.get(),
            "civil_status": self.e_civil.get(),
            "contact": self.e_contact.get(),
            "occupation": self.e_occupation.get(),
            "voter_status": self.e_voter.get(),
            "emergency_contact": self.e_emerg.get(),
            "purok": self.e_purok.get(),
        }

        try:
            res = requests.put(f"{self.api_base}/resident/{rid}", json=data, timeout=6)
            if res.status_code in (200, 201):
                messagebox.showinfo("Updated", "Resident updated successfully")
                self.clear_form()
                self.load_residents()
            else:
                messagebox.showerror("Error", f"Failed to update resident: {res.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to server:\n{e}")

    def do_delete(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a resident first")
            return

        rid = self.tree.item(sel, "values")[0]
        if not messagebox.askyesno("Confirm", "Delete selected resident?"):
            return

        try:
            res = requests.delete(f"{self.api_base}/resident/{rid}", timeout=6)
            if res.status_code in (200, 201):
                messagebox.showinfo("Deleted", "Resident deleted")
                self.clear_form()
                self.load_residents()
            else:
                messagebox.showerror("Error", "Failed to delete resident")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to server:\n{e}")

    def on_tree_select(self, event):
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")

        self.e_first.delete(0, tk.END);
        self.e_first.insert(0, vals[1])
        self.e_middle.delete(0, tk.END);
        self.e_middle.insert(0, vals[2])
        self.e_last.delete(0, tk.END);
        self.e_last.insert(0, vals[3])
        self.e_ext.set(vals[4] if vals[4] else "N/A")
        self.e_gender.set(vals[5])
        self.e_birth.delete(0, tk.END);
        self.e_birth.insert(0, vals[6])
        self.e_civil.set(vals[7])
        self.e_contact.delete(0, tk.END);
        self.e_contact.insert(0, vals[8])
        self.e_occupation.delete(0, tk.END);
        self.e_occupation.insert(0, vals[9])
        self.e_voter.set(vals[10])
        self.e_emerg.delete(0, tk.END);
        self.e_emerg.insert(0, vals[11])
        self.e_purok.set(vals[12])

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.apply_filter()

    def clear_form(self):
        self.e_first.delete(0, tk.END)
        self.e_middle.delete(0, tk.END)
        self.e_last.delete(0, tk.END)
        self.e_ext.set("N/A")
        self.e_gender.set("")
        self.e_birth.delete(0, tk.END)
        self.e_civil.set("")
        self.e_contact.delete(0, tk.END)
        self.e_occupation.delete(0, tk.END)
        self.e_voter.set("")
        self.e_emerg.delete(0, tk.END)
        self.e_purok.set("")