import tkinter as tk
from tkinter import ttk, messagebox
import requests


class RegisterWindow:
    def __init__(self, parent, api_base):
        self.api_base = api_base

        # Create a popup window (Toplevel)
        self.win = tk.Toplevel(parent)
        self.win.title("Register New Account")
        self.win.geometry("400x350")

        # Center the window roughly
        self.win.update_idletasks()
        width = self.win.winfo_width()
        height = self.win.winfo_height()
        x = (self.win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.win.winfo_screenheight() // 2) - (height // 2)
        self.win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        self.build_ui()

    def build_ui(self):
        # Header
        tk.Label(self.win, text="Create Account", font=("Segoe UI", 14, "bold")).pack(pady=15)

        form_frame = tk.Frame(self.win)
        form_frame.pack(padx=20, pady=5)

        # Username
        tk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_user = tk.Entry(form_frame, width=30)
        self.entry_user.grid(row=0, column=1, pady=5)

        # Password
        tk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_pw = tk.Entry(form_frame, show="*", width=30)
        self.entry_pw.grid(row=1, column=1, pady=5)

        # Confirm Password
        tk.Label(form_frame, text="Confirm Pass:").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_confirm = tk.Entry(form_frame, show="*", width=30)
        self.entry_confirm.grid(row=2, column=1, pady=5)

        # Role
        tk.Label(form_frame, text="Role:").grid(row=3, column=0, sticky="w", pady=5)
        self.combo_role = ttk.Combobox(form_frame, values=["Staff", "Admin"], state="readonly", width=27)
        self.combo_role.set("Staff")
        self.combo_role.grid(row=3, column=1, pady=5)

        # Buttons
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Register", width=15, bg="#4CAF50", fg="white", command=self.do_register).pack(
            side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=self.win.destroy).pack(side="left", padx=5)

    def do_register(self):
        username = self.entry_user.get().strip()
        password = self.entry_pw.get().strip()
        confirm = self.entry_confirm.get().strip()
        role = self.combo_role.get()

        # Validation
        if not username or not password:
            messagebox.showwarning("Required", "Username and Password are required.", parent=self.win)
            return

        if password != confirm:
            messagebox.showerror("Mismatch", "Passwords do not match.", parent=self.win)
            return

        # Send to Server
        payload = {
            "username": username,
            "password": password,
            "role": role
        }

        try:
            res = requests.post(f"{self.api_base}/register", json=payload)
            if res.status_code == 200:
                messagebox.showinfo("Success", "Account created successfully! You can now login.", parent=self.win)
                self.win.destroy()  # Close the registration window
            else:
                try:
                    err = res.json().get("error", "Unknown error")
                except:
                    err = res.text
                messagebox.showerror("Registration Failed", f"Error: {err}", parent=self.win)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server.\n{e}", parent=self.win)