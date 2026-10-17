import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Import Tabs
from residents_tab import ResidentsTab
from blotters_tab import BlottersTab
from households_tab import HouseholdsTab
from voters_tab import VotersTab
from dashboard import DashboardTab
from certificates_tab import CertificatesTab
from officials_tab import OfficialsTab

# Import Register
from register import RegisterWindow

# Default Configuration (Will be updated by the UI)
SERVER_IP = "127.0.0.1"
BASE_URL = f"http://{SERVER_IP}:5000"
session_user = None

# -------------------------------------------------------------
#  MODERN THEME CONFIGURATION (The "CSS")
# -------------------------------------------------------------
COLORS = {
    "bg_main": "#F0F2F5",
    "bg_card": "#FFFFFF",
    "primary": "#1877F2",
    "primary_hover": "#166FE5",
    "secondary": "#42B72A",
    "secondary_hover": "#36A420",
    "danger": "#FF3B30",
    "danger_hover": "#D32F2F",
    "warning": "#FF9500",
    "warning_hover": "#E08900",
    "text_dark": "#1C1E21",
    "text_light": "#65676B",
    "header_bg": "#242526",
    "header_text": "#E4E6EB"
}

FONTS = {
    "h1": ("Segoe UI", 20, "bold"),
    "h2": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 10),
    "bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9)
}


def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')

    # Notebook (Tabs) Styling
    style.configure("TNotebook", background=COLORS["bg_main"], borderwidth=0)
    style.configure("TNotebook.Tab",
                    font=FONTS["bold"],
                    padding=[15, 8],
                    background="#E4E6EB",
                    foreground=COLORS["text_dark"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["bg_card"])],
              foreground=[("selected", COLORS["primary"])])

    # Treeview (Table) Styling
    style.configure("Treeview",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_dark"],
                    fieldbackground=COLORS["bg_card"],
                    rowheight=30,
                    font=FONTS["body"],
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    font=FONTS["bold"],
                    background=COLORS["bg_main"],
                    foreground=COLORS["text_dark"],
                    relief="flat")
    style.map("Treeview", background=[('selected', COLORS["primary"])])

    # Combobox
    style.configure("TCombobox", padding=5)


# -------------------------------------------------------------
# CUSTOM ROUNDED BUTTON COMPONENT
# -------------------------------------------------------------
class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, corner_radius, padding=0,
                 color="#FFFFFF", hover_color=None, bg_color="#FFFFFF",
                 text="", command=None, text_color="black"):
        tk.Canvas.__init__(self, parent, borderwidth=0, relief="flat",
                           highlightthickness=0, bg=bg_color)
        self.command = command
        self.color = color
        self.hover_color = hover_color if hover_color else color
        self.text_color = text_color
        self.width = width
        self.height = height

        # Determine geometry
        self.configure(width=width, height=height)

        # Draw the rounded shape (using a smoothed polygon hack for Tkinter)
        self.id_shape = self.create_polygon(
            self._get_rounded_points(padding, padding, width - padding, height - padding, corner_radius),
            fill=color, outline=color, smooth=True
        )

        # Draw the text
        self.id_text = self.create_text(width / 2, height / 2, text=text,
                                        fill=text_color, font=FONTS["bold"])

        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _get_rounded_points(self, x1, y1, x2, y2, r):
        return [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
                x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
                x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]

    def _on_enter(self, event):
        self.itemconfigure(self.id_shape, fill=self.hover_color, outline=self.hover_color)

    def _on_leave(self, event):
        self.itemconfigure(self.id_shape, fill=self.color, outline=self.color)

    def _on_click(self, event):
        # Optional: Click effect (darken slightly or move)
        self.move(self.id_text, 1, 1)

    def _on_release(self, event):
        self.move(self.id_text, -1, -1)
        if self.command:
            self.command()

    def config(self, **kwargs):
        """Allow configuring command dynamically."""
        if 'command' in kwargs:
            self.command = kwargs['command']


# -------------------------------------------------------------
# LOGIN WINDOW
# -------------------------------------------------------------
root = tk.Tk()
root.title("Barangay Felifee")
root.geometry("1100x750")
root.configure(bg=COLORS["bg_main"])
setup_styles()

# Wrapper to center the login card
login_container = tk.Frame(root, bg=COLORS["bg_main"])
login_container.pack(expand=True, fill="both")

# The "Card" for Login
login_frame = tk.Frame(login_container, bg=COLORS["bg_card"], padx=40, pady=40)
login_frame.place(relx=0.5, rely=0.5, anchor="center")

# -- UI Elements --
# Logo/Title Area
tk.Label(login_frame, text="Barangay System", font=("Segoe UI", 24, "bold"),
         bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(pady=(0, 5))

tk.Label(login_frame, text="Sign in to your account", font=FONTS["small"],
         bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(pady=(0, 20))

# Input Fields
input_frame = tk.Frame(login_frame, bg=COLORS["bg_card"])
input_frame.pack(fill="x", pady=(0, 5))

# --- SERVER IP FIELD (Added for Multiple Devices) ---
tk.Label(input_frame, text="Server IP", font=FONTS["bold"], bg=COLORS["bg_card"], fg=COLORS["text_dark"]).pack(
    anchor="w")
entry_ip = tk.Entry(input_frame, width=32, font=("Segoe UI", 11), relief="flat", bg="#F0F2F5", bd=5)
entry_ip.pack(pady=(5, 10), ipady=3, fill="x")
entry_ip.insert(0, "127.0.0.1")  # Default to localhost

# --- USERNAME ---
tk.Label(input_frame, text="Username", font=FONTS["bold"], bg=COLORS["bg_card"], fg=COLORS["text_dark"]).pack(
    anchor="w")
entry_user = tk.Entry(input_frame, width=32, font=("Segoe UI", 11), relief="flat", bg="#F0F2F5", bd=5)
entry_user.pack(pady=(5, 10), ipady=3, fill="x")

# --- PASSWORD ---
tk.Label(input_frame, text="Password", font=FONTS["bold"], bg=COLORS["bg_card"], fg=COLORS["text_dark"]).pack(
    anchor="w")
entry_pw = tk.Entry(input_frame, show="*", width=32, font=("Segoe UI", 11), relief="flat", bg="#F0F2F5", bd=5)
entry_pw.pack(pady=(5, 15), ipady=3, fill="x")


def do_login():
    global SERVER_IP, BASE_URL, session_user

    # 1. Update Server IP from Input
    server_ip_input = entry_ip.get().strip()
    if server_ip_input:
        SERVER_IP = server_ip_input
        BASE_URL = f"http://{SERVER_IP}:5000"

    username = entry_user.get()
    password = entry_pw.get()

    if not username or not password:
        messagebox.showwarning("Login", "Enter username and password")
        return

    try:
        # 2. Use the updated BASE_URL
        res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            session_user = res.json()["user"]
            login_container.pack_forget()  # Hide login container
            build_main_ui()  # Show App
        else:
            messagebox.showerror("Login Failed", res.json().get("error", "Invalid credentials"))
    except Exception as e:
        messagebox.showerror("Connection Error", f"Could not connect to server at {SERVER_IP}.\n\nError: {e}")


def open_register():
    global SERVER_IP, BASE_URL
    # Ensure registration uses the typed IP too
    server_ip_input = entry_ip.get().strip()
    if server_ip_input:
        SERVER_IP = server_ip_input
        BASE_URL = f"http://{SERVER_IP}:5000"

    RegisterWindow(root, BASE_URL)


# Buttons (Using RoundedButton)
btn_login = RoundedButton(login_frame, width=300, height=45, corner_radius=20,
                          color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                          bg_color=COLORS["bg_card"], text_color="white",
                          text="Login", command=do_login)
btn_login.pack(pady=5)

btn_reg = RoundedButton(login_frame, width=300, height=45, corner_radius=20,
                        color=COLORS["secondary"], hover_color=COLORS["secondary_hover"],
                        bg_color=COLORS["bg_card"], text_color="white",
                        text="Create New Account", command=open_register)
btn_reg.pack(pady=5)


# -------------------------------------------------------------
# MAIN UI BUILDER
# -------------------------------------------------------------
def build_main_ui():
    # Main Container
    main_frame = tk.Frame(root, bg=COLORS["bg_main"])
    main_frame.pack(fill="both", expand=True)

    # === HEADER ===
    header = tk.Frame(main_frame, bg=COLORS["header_bg"], height=65)
    header.pack(fill="x", side="top")
    header.pack_propagate(False)

    # Header Content Wrapper
    header_content = tk.Frame(header, bg=COLORS["header_bg"], padx=20)
    header_content.pack(fill="both", expand=True)

    # 1. Branding / Welcome
    user_role = session_user.get('role', 'Staff')
    user_name = session_user.get('username', 'User')

    # Left side of header
    title_frame = tk.Frame(header_content, bg=COLORS["header_bg"])
    title_frame.pack(side="left", pady=10)

    tk.Label(title_frame, text="Barangay Felifee Resident Management System", bg=COLORS["header_bg"], fg="white",
             font=("Segoe UI", 16, "bold")).pack(side="left", padx=(0, 15))

    tk.Label(title_frame, text=f"{user_name}", bg=COLORS["header_bg"], fg=COLORS["header_text"],
             font=FONTS["bold"]).pack(side="left")

    tk.Label(title_frame, text=f"   {user_role}", bg=COLORS["header_bg"], fg="#888",
             font=FONTS["small"]).pack(side="left")

    # 2. Header Buttons (Right side)
    header_btns = tk.Frame(header_content, bg=COLORS["header_bg"])
    header_btns.pack(side="right", pady=12)

    # Rounded Buttons for Header
    btn_refresh = RoundedButton(header_btns, width=110, height=36, corner_radius=18,
                                color=COLORS["warning"], hover_color=COLORS["warning_hover"],
                                bg_color=COLORS["header_bg"], text_color="black",
                                text="Refresh Data", command=None)  # Command set later
    btn_refresh.pack(side="left", padx=5)

    def do_logout():
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            main_frame.destroy()
            login_container.pack(expand=True, fill="both")
            entry_user.delete(0, tk.END)
            entry_pw.delete(0, tk.END)
            global session_user
            session_user = None

    btn_logout = RoundedButton(header_btns, width=90, height=36, corner_radius=18,
                               color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                               bg_color=COLORS["header_bg"], text_color="white",
                               text="Logout", command=do_logout)
    btn_logout.pack(side="left", padx=5)

    # === TABS CONTAINER ===
    content_area = tk.Frame(main_frame, bg=COLORS["bg_main"], padx=15, pady=15)
    content_area.pack(fill="both", expand=True)

    notebook = ttk.Notebook(content_area)
    notebook.pack(fill="both", expand=True)

    # 1. Dashboard
    dash_tab = DashboardTab(notebook, BASE_URL)
    notebook.add(dash_tab.tab, text=" Dashboard ")

    # 2. Residents (Pass User)
    residents_tab = ResidentsTab(notebook, BASE_URL, session_user)
    notebook.add(residents_tab.tab, text=" Residents ")

    # 3. Certificates (Pass User)
    certs_tab = CertificatesTab(notebook, BASE_URL, session_user)
    notebook.add(certs_tab.tab, text=" Certificates ")

    # 4. Blotters (Pass User)
    blotters_tab = BlottersTab(notebook, BASE_URL, session_user)
    notebook.add(blotters_tab.tab, text=" Blotter Cases ")

    # 5. Households (Pass User)
    households_tab = HouseholdsTab(notebook, BASE_URL, session_user)
    notebook.add(households_tab.tab, text=" Households ")

    # 6. Voters
    voters_tab = VotersTab(notebook, BASE_URL)
    notebook.add(voters_tab.tab, text=" Voter's List ")

    # 7. Officials
    officials_tab = OfficialsTab(notebook, BASE_URL, session_user)
    notebook.add(officials_tab.tab, text=" Officials ")

    # === DYNAMIC REFRESH LOGIC ===
    def refresh_all_data():
        try:
            dash_tab.load_data()
            residents_tab.load_residents()
            voters_tab.load_voters()
            blotters_tab.load_blotters()
            blotters_tab.reload_residents()
            households_tab.load_households()
            households_tab.load_heads()

            # Refresh officials only if the tab exists
            if officials_tab:
                officials_tab.load_officials()

            certs_tab.load_data()
            messagebox.showinfo("Refreshed", "System data updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Refresh failed: {e}")

    # Set the command for the refresh button we created earlier
    btn_refresh.config(command=refresh_all_data)


# -------------------------------------------------------------
# RUN APP
# -------------------------------------------------------------
if __name__ == "__main__":
    root.mainloop()