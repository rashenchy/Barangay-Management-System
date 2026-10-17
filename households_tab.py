import tkinter as tk
from tkinter import ttk, messagebox
import requests


class HouseholdsTab:
    RELATIONSHIP_OPTIONS = [
        "Head",
        "Spouse",
        "Child",
        "Sibling",
        "Father",
        "Mother",
        "Grandparent",
        "Other",
    ]

    def __init__(self, parent, api_base, user_session):
        self.parent = parent
        self.api_base = api_base.rstrip("/")
        self.user_session = user_session
        self.tab = tk.Frame(self.parent)
        self.residents = []
        self.households = []
        self.build_tab()

    # ---------------------------------------------------
    # MAIN TAB UI
    # ---------------------------------------------------
    def build_tab(self):
        top = tk.Frame(self.tab)
        top.pack(fill="x", padx=8, pady=5)

        tk.Label(top, text="Head of Household:").pack(side="left", padx=(0, 4))

        # SEARCHABLE COMBOBOX
        self.head_combo = ttk.Combobox(top, width=30)
        self.head_combo.pack(side="left", padx=4)
        self.head_combo.bind("<KeyRelease>", self.filter_head_combo)

        self.purok_label = tk.Label(top, text="")
        self.purok_label.pack(side="left", padx=4)

        tk.Button(top, text="Add Household", command=self.add_household).pack(
            side="left", padx=10
        )
        tk.Button(top, text="Edit Household", command=self.edit_household).pack(
            side="left", padx=5
        )

        # --- CHANGED: Only show delete if Admin ---
        if self.user_session.get("role") == "Admin":
            tk.Button(top, text="Delete Household", command=self.delete_household, bg="#FF3B30", fg="white").pack(
                side="left", padx=5
            )
        # ------------------------------------------

        tk.Button(top, text="View Details", command=self.view_details).pack(
            side="left", padx=5
        )

        columns = ("household_id", "head_name", "purok", "members")
        self.tree = ttk.Treeview(self.tab, columns=columns, show="headings")
        self.tree.heading("household_id", text="Household No.")
        self.tree.heading("head_name", text="Head of Household")
        self.tree.heading("purok", text="Purok")
        self.tree.heading("members", text="Members")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.load_heads()
        self.load_households()

        self.head_combo.bind("<<ComboboxSelected>>", self.update_purok_label)

    # ---------------------------------------------------
    # FILTER FUNCTION FOR SEARCH
    # ---------------------------------------------------
    def filter_head_combo(self, event):
        if event.keysym in ["Return", "Up", "Down", "Left", "Right"]:
            return

        typed = self.head_combo.get().lower()
        all_options = []
        for r in self.residents:
            ext = r.get("extension", "")
            if ext == "N/A": ext = ""
            full = f"{r['id']} - {r['first_name']} {r['middle_name']} {r['last_name']} {ext}"
            all_options.append(" ".join(full.split()))

        if typed == "":
            self.head_combo["values"] = all_options
        else:
            filtered = [item for item in all_options if typed in item.lower()]
            self.head_combo["values"] = filtered

    # ---------------------------------------------------
    # LOAD RESIDENTS
    # ---------------------------------------------------
    def load_heads(self):
        try:
            res = requests.get(f"{self.api_base}/residents")
            res.raise_for_status()
            self.residents = res.json()
            # Populate initial list
            self.head_combo["values"] = []
            vals = []
            for r in self.residents:
                ext = r.get("extension", "")
                if ext == "N/A": ext = ""
                # Helper to clean up extra spaces if middle name or ext is missing
                full = f"{r['id']} - {r['first_name']} {r['middle_name']} {r['last_name']} {ext}"
                vals.append(" ".join(full.split()))  # Removes extra whitespace
            self.head_combo["values"] = vals
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load residents:\n{e}")

    def update_purok_label(self, event=None):
        head = self.head_combo.get()
        if not head:
            self.purok_label.config(text="")
            return

        try:
            res_id = head.split(" - ")[0]
            resident = next((r for r in self.residents if str(r["id"]) == res_id), None)
            self.purok_label.config(text=resident.get("purok", "") if resident else "")
        except:
            self.purok_label.config(text="")

    # ---------------------------------------------------
    # LOAD HOUSEHOLDS
    # ---------------------------------------------------
    def load_households(self):
        try:
            res = requests.get(f"{self.api_base}/households")
            res.raise_for_status()
            self.households = res.json()

            self.tree.delete(*self.tree.get_children())
            for h in self.households:
                members = h.get("members", 0)
                self.tree.insert(
                    "",
                    "end",
                    iid=str(h["id"]),
                    values=(
                        h["id"],
                        h.get("head_name", ""),
                        h.get("purok", ""),
                        members,
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load households:\n{e}")

    # ---------------------------------------------------
    # ADD HOUSEHOLD
    # ---------------------------------------------------
    def add_household(self):
        head = self.head_combo.get()
        if not head:
            messagebox.showwarning("Input", "Select head of household")
            return

        try:
            head_id = head.split(" - ")[0]
            purok = self.purok_label.cget("text")
            res = requests.post(
                f"{self.api_base}/household", json={"head_id": head_id, "purok": purok}
            )
            res.raise_for_status()
            messagebox.showinfo("Success", "Household added")
            self.load_households()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add:\n{e}")

    # ---------------------------------------------------
    # EDIT HOUSEHOLD
    # ---------------------------------------------------
    def edit_household(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a household to edit")
            return

        hid = selected[0]
        hdata = next((h for h in self.households if str(h["id"]) == hid), None)
        if not hdata:
            messagebox.showerror("Error", "Household not found")
            return

        win = tk.Toplevel(self.tab)
        win.title("Edit Household")

        tk.Label(win, text="Head:").grid(row=0, column=0, padx=5, pady=5)
        edit_head = ttk.Combobox(win, width=30)
        edit_head.grid(row=0, column=1)
        edit_head["values"] = self.head_combo["values"]
        edit_head.set(hdata["head_name"])

        tk.Label(win, text="Purok:").grid(row=1, column=0, padx=5, pady=5)
        edit_purok = tk.Entry(win)
        edit_purok.grid(row=1, column=1)
        edit_purok.insert(0, hdata.get("purok", ""))

        def save_change():
            try:
                head_txt = edit_head.get()
                if " - " in head_txt:
                    head_id = head_txt.split(" - ")[0]
                else:
                    head_id = head_txt.split(" - ")[0]

                purok = edit_purok.get()
                res = requests.put(
                    f"{self.api_base}/household/{hid}",
                    json={"head_id": head_id, "purok": purok},
                )
                res.raise_for_status()
                messagebox.showinfo("Updated", "Household updated")
                win.destroy()
                self.load_households()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update (ensure ID is selected):\n{e}")

        tk.Button(win, text="Save", command=save_change).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    # ---------------------------------------------------
    # DELETE HOUSEHOLD
    # ---------------------------------------------------
    def delete_household(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select household to delete")
            return

        hid = selected[0]
        if not messagebox.askyesno("Confirm", "Delete this household?"):
            return

        try:
            res = requests.delete(f"{self.api_base}/household/{hid}")
            res.raise_for_status()
            messagebox.showinfo("Deleted", "Household deleted")
            self.load_households()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete:\n{e}")

    # ---------------------------------------------------
    # VIEW DETAILS
    # ---------------------------------------------------
    def view_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a household to view details")
            return
        hid = selected[0]
        try:
            res = requests.get(f"{self.api_base}/household/{hid}")
            res.raise_for_status()
            hdata = res.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load details:\n{e}")
            return

        # ---------------- WINDOW ----------------
        top = tk.Toplevel(self.tab)
        top.title(f"Household {hid} Details")
        top.geometry("900x520")

        # HEADER
        tk.Label(top, text=f"Household ID: {hdata.get('id')}").pack(anchor="w")
        tk.Label(top, text=f"Head: {hdata.get('head_name')}").pack(anchor="w")
        tk.Label(top, text=f"Purok: {hdata.get('purok')}").pack(anchor="w")
        tk.Label(top, text=f"Members: {len(hdata.get('members', []))}").pack(anchor="w")
        ttk.Separator(top).pack(fill="x", pady=5)

        # -----------------------------------------
        # MEMBERS TABLE (UPDATED)
        # -----------------------------------------
        columns = ("relationship", "full_name", "mem_id")
        member_tree = ttk.Treeview(top, columns=columns, show="headings")

        member_tree.heading("relationship", text="Relation")
        member_tree.heading("full_name", text="Full Name")

        # Hide the ID column
        member_tree.column("mem_id", width=0, stretch=False)

        member_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # SAFE INSERT (UPDATED)
        for m in hdata.get("members", []):
            relationship = m.get("relationship") or "Unknown"
            full_name = m.get("full_name") or "Unnamed"
            rid = m.get("resident_id") or m.get("id")
            mem_pk = m.get("id")
            if rid is None:
                continue
            member_tree.insert(
                "", "end", iid=str(rid), values=(relationship, full_name, mem_pk)
            )

        # -----------------------------------------
        # ADD MEMBER
        # -----------------------------------------
        add_frame = tk.Frame(top)
        add_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(add_frame, text="Add Member:").pack(side="left")

        member_combo = ttk.Combobox(add_frame, width=25)

        m_vals = []
        for r in self.residents:
            ext = r.get("extension", "")
            if ext == "N/A": ext = ""
            full = f"{r['id']} - {r['first_name']} {r['middle_name']} {r['last_name']} {ext}"
            m_vals.append(" ".join(full.split()))
        member_combo["values"] = m_vals
        member_combo.pack(side="left", padx=4)

        # --- [START] NEW FILTER LOGIC ---
        def filter_member(event):
            if event.keysym in ["Return", "Up", "Down", "Left", "Right"]:
                return
            typed = member_combo.get().lower()
            if typed == "":
                member_combo["values"] = m_vals
            else:
                filtered = [item for item in m_vals if typed in item.lower()]
                member_combo["values"] = filtered

        member_combo.bind("<KeyRelease>", filter_member)

        tk.Label(add_frame, text="Relationship:").pack(side="left")
        rel_combo = ttk.Combobox(add_frame, values=self.RELATIONSHIP_OPTIONS, width=15)
        rel_combo.set("")  # no default value shown
        rel_combo.pack(side="left")

        # -----------------------------------------
        # ADD MEMBER ACTION (UPDATED REFRESH)
        # -----------------------------------------
        def add_member():
            sel = member_combo.get()
            if not sel:
                messagebox.showwarning("Input", "Select resident first")
                return
            try:
                rid = sel.split(" - ")[0]
                relationship = rel_combo.get()
                res = requests.post(
                    f"{self.api_base}/household/{hid}/member",
                    json={"resident_id": rid, "relationship": relationship},
                )
                res.raise_for_status()

                # REFRESH MEMBER LIST
                member_tree.delete(*member_tree.get_children())
                res = requests.get(f"{self.api_base}/household/{hid}")
                updated = res.json()
                for m in updated.get("members", []):
                    full_name = m.get("full_name", "Unnamed")
                    rel = m.get("relationship", "Unknown")
                    mid = m.get("resident_id")
                    mem_pk = m.get("id")  # Capture PK
                    member_tree.insert("", "end", iid=str(mid), values=(rel, full_name, mem_pk))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add member:\n{e}")

        tk.Button(add_frame, text="Add", command=add_member).pack(side="left", padx=5)

        # -----------------------------------------
        # EDIT MEMBER (UPDATED REFRESH)
        # -----------------------------------------
        def edit_member_action():
            sel = member_tree.selection()
            if not sel:
                messagebox.showwarning("Select", "Select a member to edit")
                return
            rid = sel[0]
            current_rel = member_tree.item(rid, "values")[0]

            rel_win = tk.Toplevel(top)
            rel_win.title("Edit Relationship")

            tk.Label(rel_win, text="Relationship:").pack(padx=10, pady=5)
            rel_edit = ttk.Combobox(rel_win, values=self.RELATIONSHIP_OPTIONS)
            rel_edit.set(current_rel)
            rel_edit.pack(padx=10, pady=5)

            def save_rel():
                new_rel = rel_edit.get()
                try:
                    # Note: Update uses resident_id (rid), which is correct for server.py logic
                    res = requests.put(
                        f"{self.api_base}/household/{hid}/member/{rid}",
                        json={"relationship": new_rel},
                    )
                    res.raise_for_status()
                    rel_win.destroy()

                    # REFRESH MEMBER LIST
                    member_tree.delete(*member_tree.get_children())
                    res = requests.get(f"{self.api_base}/household/{hid}")
                    updated = res.json()
                    for m in updated.get("members", []):
                        full_name = m.get("full_name", "Unnamed")
                        rel = m.get("relationship", "Unknown")
                        mid = m.get("resident_id")
                        mem_pk = m.get("id")  # Capture PK
                        member_tree.insert(
                            "", "end", iid=str(mid), values=(rel, full_name, mem_pk)
                        )
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update:\n{e}")

            tk.Button(rel_win, text="Save", command=save_rel).pack(pady=10)

        # -----------------------------------------
        # REMOVE MEMBER (FIXED LOGIC)
        # -----------------------------------------
        def remove_member_action():
            sel = member_tree.selection()
            if not sel:
                messagebox.showwarning("Select", "Select a member to remove")
                return

            rid = sel[0]

            vals = member_tree.item(rid, "values")
            mem_pk = vals[2]

            if not messagebox.askyesno("Confirm", "Remove selected member?"):
                return

            try:
                res = requests.delete(f"{self.api_base}/household/{hid}/member/{mem_pk}")
                res.raise_for_status()

                # REFRESH MEMBER LIST
                member_tree.delete(*member_tree.get_children())
                res = requests.get(f"{self.api_base}/household/{hid}")
                updated = res.json()
                for m in updated.get("members", []):
                    full_name = m.get("full_name", "Unnamed")
                    rel = m.get("relationship", "Unknown")
                    mid = m.get("resident_id")
                    mem_pk_new = m.get("id")  # Capture PK
                    member_tree.insert("", "end", iid=str(mid), values=(rel, full_name, mem_pk_new))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove member:\n{e}")

        # BUTTONS FOR EDIT / REMOVE
        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x", pady=5)

        tk.Button(
            btn_frame, text="Edit Selected Member", command=edit_member_action
        ).pack(side="right", padx=10)

        # --- CHANGED: Only show remove if Admin ---
        if self.user_session.get("role") == "Admin":
            tk.Button(
                btn_frame, text="Remove Selected Member", command=remove_member_action, bg="#FF3B30", fg="white"
            ).pack(side="right", padx=10)
        # ------------------------------------------