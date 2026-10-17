import tkinter as tk
from tkinter import ttk, messagebox
import requests
import webbrowser
import os
import tempfile
from datetime import datetime

# --- NEW IMPORTS FOR PDF GENERATION ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

class CertificatesTab:
    def __init__(self, parent, api_base, user_session):
        self.parent = parent
        self.api_base = api_base
        self.user_session = user_session
        self.tab = tk.Frame(self.parent)
        self.residents = []
        self.officials = {}
        self.build_ui()

    def build_ui(self):
        # Header
        tk.Label(self.tab, text="Issue Certificates (PDF)", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # 1. Select Resident
        sel_frame = tk.LabelFrame(self.tab, text="1. Select Resident", padx=10, pady=10)
        sel_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(sel_frame, text="Search Resident:").pack(side="left")
        self.combo_res = ttk.Combobox(sel_frame, width=40)
        self.combo_res.pack(side="left", padx=5)
        self.combo_res.bind("<KeyRelease>", self.filter_residents)

        # 2. Certificate Details
        det_frame = tk.LabelFrame(self.tab, text="2. Document Details", padx=10, pady=10)
        det_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(det_frame, text="Type:").grid(row=0, column=0, sticky="e", pady=5)
        self.combo_type = ttk.Combobox(det_frame, values=["Barangay Clearance", "Certificate of Indigency",
                                                          "Certificate of Residency"], state="readonly", width=30)
        self.combo_type.grid(row=0, column=1, sticky="w", padx=5)
        self.combo_type.current(0)

        tk.Label(det_frame, text="Purpose:").grid(row=1, column=0, sticky="e", pady=5)
        self.ent_purpose = tk.Entry(det_frame, width=40)
        self.ent_purpose.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(det_frame, text="O.R. No:").grid(row=2, column=0, sticky="e", pady=5)
        self.ent_or = tk.Entry(det_frame, width=20)
        self.ent_or.grid(row=2, column=1, sticky="w", padx=5)

        tk.Label(det_frame, text="Amount Paid:").grid(row=3, column=0, sticky="e", pady=5)
        self.ent_amount = tk.Entry(det_frame, width=20)
        self.ent_amount.insert(0, "0.00")
        self.ent_amount.grid(row=3, column=1, sticky="w", padx=5)

        # 3. Actions
        btn_frame = tk.Frame(self.tab)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Generate PDF", bg="#F44336", fg="white", width=20, font=("Arial", 11, "bold"),
                  command=self.generate_document).pack(side="left", padx=10)

        self.load_data()

    def load_data(self):
        # Load Residents
        try:
            r = requests.get(f"{self.api_base}/residents")
            self.residents = r.json()
            self.update_combo_list(self.residents)
        except:
            pass

        # Load Officials for the document signature
        try:
            o = requests.get(f"{self.api_base}/officials")
            data = o.json()
            for off in data:
                self.officials[off['position']] = off['full_name']
        except:
            pass

        # Load Next OR Number
        self.fetch_next_or()

    def fetch_next_or(self):
        try:
            r = requests.get(f"{self.api_base}/certificate/next-or")
            if r.status_code == 200:
                next_or = r.json().get("next_or", 1001)
                self.ent_or.delete(0, tk.END)
                self.ent_or.insert(0, str(next_or))
        except Exception as e:
            print(f"Failed to fetch next OR: {e}")

    def filter_residents(self, event):
        if event.keysym in ["Return", "Up", "Down"]: return
        typed = self.combo_res.get().lower()
        if not typed:
            self.update_combo_list(self.residents)
            return

        # FIXED: Added check for middle_name
        filtered = [
            r for r in self.residents
            if typed in r['first_name'].lower()
               or typed in str(r.get('middle_name', '')).lower()
               or typed in r['last_name'].lower()
               or typed in str(r['id'])
        ]
        self.update_combo_list(filtered)

    def update_combo_list(self, data):
        vals = []
        for r in data:
            ext = r.get("extension", "")
            if ext and ext != "N/A":
                name = f"{r['id']} - {r['first_name']} {r['last_name']} {ext}"
            else:
                name = f"{r['id']} - {r['first_name']} {r['last_name']}"
            vals.append(name)
        self.combo_res['values'] = vals

    def generate_document(self):
        sel = self.combo_res.get()
        if not sel:
            messagebox.showwarning("Missing", "Please select a resident.")
            return

        res_id = sel.split(" - ")[0]
        # Find full resident object
        resident = next((r for r in self.residents if str(r['id']) == res_id), None)
        if not resident: return

        doc_type = self.combo_type.get()
        purpose = self.ent_purpose.get()
        or_no = self.ent_or.get()
        amount = self.ent_amount.get()

        # 1. Log to Server
        try:
            payload = {
                "resident_id": res_id,
                "certificate_type": doc_type,
                "purpose": purpose,
                "or_number": or_no,
                "amount_paid": amount,
                "issued_by": self.user_session.get("username", "admin")
            }
            requests.post(f"{self.api_base}/certificate/log", json=payload)
            # Refresh OR for next time
            self.fetch_next_or()
        except Exception as e:
            print(f"Logging failed: {e}")

        # 2. Generate PDF
        self.create_pdf_document(resident, doc_type, purpose, or_no, amount)

    # --- ADDED: Seal Background Helper ---
    def add_seal_background(self, canvas, doc):
        canvas.saveState()
        image_path = os.path.abspath("assets/XkDuCfIX.jpg")

        if os.path.exists(image_path):
            # 1. Define Position & Size (Bottom Right, behind Captain)
            img_w = 160
            img_h = 160

            x = 340
            y = 100

            # 2. Circular Mask (To remove square background)
            path = canvas.beginPath()
            cx = x + (img_w / 2)
            cy = y + (img_h / 2)
            radius = img_w / 2
            path.circle(cx, cy, radius)
            canvas.clipPath(path, stroke=0)

            # 3. Draw Image with Transparency
            canvas.setFillAlpha(0.3)
            canvas.drawImage(image_path, x, y, width=img_w, height=img_h, mask=None, preserveAspectRatio=True)

        else:
            print(f"Seal image not found at: {image_path}")

        canvas.restoreState()

    def create_pdf_document(self, resident, doc_type, purpose, or_no, amount):
        # 1. Prepare Data
        captain = self.officials.get("Barangay Captain", "Donald Trump").upper()
        secretary = self.officials.get("Barangay Secretary", "Lara Bayan").upper()
        full_name = f"{resident['first_name']} {resident['middle_name']} {resident['last_name']} {resident.get('extension', '')}".upper()
        civil_status = resident.get('civil_status', '')
        purok = resident.get('purok', '')

        # 2. Create Temp File
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        # 3. Setup ReportLab Document
        doc = SimpleDocTemplate(path, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=50)

        story = []
        styles = getSampleStyleSheet()

        # Define Custom Styles
        style_center = ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica',
                                      fontSize=12, leading=14)
        style_title = ParagraphStyle(name='Title', parent=styles['Normal'], alignment=TA_CENTER,
                                     fontName='Helvetica-Bold', fontSize=18, spaceAfter=20, spaceBefore=20)
        style_body = ParagraphStyle(name='Body', parent=styles['Normal'], alignment=TA_JUSTIFY, fontName='Helvetica',
                                    fontSize=12, leading=18, spaceAfter=12)
        style_footer = ParagraphStyle(name='Footer', parent=styles['Normal'], fontSize=10, leading=12)

        # --- HEADER ---
        header_text = """Republic of the Philippines<br/>
        Province of Nueva Ecija<br/>
        Municipality of Bongabon<br/>
        <b>BARANGAY FELIFEE</b>"""
        story.append(Paragraph(header_text, style_center))
        story.append(Spacer(1, 30))

        # --- TITLE ---
        story.append(Paragraph(doc_type.upper(), style_title))
        story.append(Spacer(1, 20))

        # --- BODY ---
        story.append(Paragraph("TO WHOM IT MAY CONCERN:", style_body))

        body_text = f"""THIS IS TO CERTIFY that <b>{full_name}</b>, of legal age, {civil_status}, Filipino, is a bonafide resident of this Barangay with postal address at Purok {purok}, Barangay Felifee, Bongabon, Nueva Ecija."""
        story.append(Paragraph(body_text, style_body))

        specific_text = self.get_body_text(doc_type, purpose)
        story.append(Paragraph(specific_text, style_body))

        purpose_text = f"This certification is issued upon the request of the above-named person for <b>{purpose or 'whatever legal purpose it may serve'}</b>."
        story.append(Paragraph(purpose_text, style_body))

        date_text = f"Issued this {datetime.now().strftime('%d day of %B, %Y')} at Barangay Felifee, Bongabon, Nueva Ecija."
        story.append(Paragraph(date_text, style_body))

        story.append(Spacer(1, 50))

        # --- SIGNATURES (Using a Table for Layout) ---
        sig_sec = f"Prepared by:<br/><br/><br/><b>{secretary}</b><br/>Barangay Secretary"
        sig_cap = f"<br/><br/><br/><b>HON. {captain}</b><br/>Punong Barangay"

        # Create Paragraphs for the table cells
        p_sec = Paragraph(sig_sec, style_center)
        p_cap = Paragraph(sig_cap, style_center)

        # Table Data: [[Column 1, Column 2]]
        data = [[p_sec, p_cap]]

        # Table Style
        table = Table(data, colWidths=[230, 230])  # Width in points
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(table)
        story.append(Spacer(1, 60))

        # --- FOOTER (OR Details) ---
        # REMOVED Amount Paid from display here as requested
        footer_text = f"""<b>O.R. No.:</b> {or_no}<br/>
        <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}"""
        story.append(Paragraph(footer_text, style_footer))

        # 4. Build PDF
        try:
            # --- MODIFIED: Added callback to draw the seal ---
            doc.build(story, onFirstPage=self.add_seal_background, onLaterPages=self.add_seal_background)

            # Open the PDF in default viewer
            webbrowser.open('file://' + path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

    def get_body_text(self, doc_type, purpose):
        if doc_type == "Certificate of Indigency":
            return "This is to further certify that the above-named person belongs to an Indigent Family in this Barangay."
        elif doc_type == "Barangay Clearance":
            return "This is to further certify that the above-named person has no derogatory record or pending case filed against him/her in this office."
        else:
            return "This certification is issued to verify the residency of the said person."