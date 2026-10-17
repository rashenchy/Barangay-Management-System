import tkinter as tk
from tkinter import messagebox
import random

# Complete list of 42 questions based on your module and OWASP Top 10
quiz_data = [
    {"q": "Which core principle ensures sensitive data is kept secret and only seen by authorized individuals?",
     "opts": ["Integrity", "Confidentiality", "Availability", "Authentication"], "ans": "Confidentiality"},
    {"q": "This refers to the assurance that data is accurate, complete, and has not been improperly altered.",
     "opts": ["Confidentiality", "Integrity", "Availability", "Non-Repudiation"], "ans": "Integrity"},
    {"q": "Which component ensures authorized users can access needed information and systems when required?",
     "opts": ["Confidentiality", "Integrity", "Availability", "Authorization"], "ans": "Availability"},
    {"q": "Authentication factor relying on something you possess, like a physical token or smartphone for OTPs.",
     "opts": ["Knowledge", "Possession", "Inherence", "Authorization"], "ans": "Possession"},
    {"q": "Authorization model making decisions based on characteristics of the user, resource, and environment.",
     "opts": ["RBAC", "Least Privilege", "DAC", "ABAC"], "ans": "ABAC"},
    {"q": "The systematic process of identifying, assessing, and controlling threats to an organization.",
     "opts": ["Data Classification", "Risk Management", "Information Assurance", "Access Control"],
     "ans": "Risk Management"},
    {"q": "Social engineering using fraudulent electronic communications to get users to click malicious links.",
     "opts": ["Vishing", "Tailgating", "Phishing", "Baiting"}, "ans": "Phishing"},
{"q": "A strong password practice involving a series of random, unrelated words.",
 "opts": ["Sequential numbers", "Year swapping", "Passphrases", "Site-specific words"], "ans": "Passphrases"},
{"q": "Highly protected data class including credit card numbers and biometric identifiers.",
 "opts": ["Public data", "Internal data", "Confidential data", "Restricted data"], "ans": "Restricted data"},
{"q": "Access control policy with strict, centralized control for high-security environments.",
 "opts": ["RBAC", "MAC", "DAC", "ABAC"], "ans": "MAC"},
{"q": "Domain focusing on secure software and preventing vulnerabilities like input validation errors.",
 "opts": ["Networking", "System Admin", "Program Fundamentals", "Platform Tech"], "ans": "Program Fundamentals"},
{"q": "Web systems security concern involving protecting applications from malicious scripts.",
 "opts": ["Physical Plant", "Web Systems", "System Admin", "Systems Integration"], "ans": "Web Systems"},
{"q": "Cryptographic algorithm using the same key for both encryption and decryption.",
 "opts": ["Asymmetric", "Symmetric", "Hashing", "Steganography"], "ans": "Symmetric"},
{"q": "An additive shift cipher (like Caesar cipher) is an example of what?",
 "opts": ["Polyalphabetic", "Transposition", "Monoalphabetic", "Block cipher"], "ans": "Monoalphabetic"},
{"q": "Primary purpose of a cryptographic hash function.",
 "opts": ["Key exchange", "Hiding messages", "Data integrity", "Decryption"], "ans": "Data integrity"},
{"q": "In asymmetric cryptography, which key does Alice use to send a confidential message to Bob?",
 "opts": ["Alice's public", "Alice's private", "Bob's public", "Bob's private"], "ans": "Bob's public"},
{"q": "Untrusted data sent to an interpreter as part of a command or query.",
 "opts": ["XSS", "Broken Auth", "Security Misconfiguration", "Injection"], "ans": "Injection"},
{"q": "Tricking a victim's browser into executing unwanted actions on a trusted site.",
 "opts": ["CSRF", "MitM", "Directory Traversal", "XXE"], "ans": "CSRF"},
{"q": "Stripping or cleaning user input to prevent malicious code execution.",
 "opts": ["Input Sanitization", "Obfuscation", "Output Encoding", "Parameterization"], "ans": "Input Sanitization"},
{"q": "Device monitoring network traffic and blocking it based on security rules.",
 "opts": ["Switch", "Router", "Firewall", "Load Balancer"], "ans": "Firewall"},
{"q": "What does a VPN primarily use to secure data over untrusted networks?",
 "opts": ["MAC filtering", "Encryption/Tunneling", "Antivirus", "IDS"], "ans": "Encryption/Tunneling"},
{"q": "Difference between IDS and IPS.",
 "opts": ["Internal vs External", "Detect vs Block", "Software vs Hardware", "Web vs DB"], "ans": "Detect vs Block"},
{"q": "A weakness in an information system that could be exploited.",
 "opts": ["Threat", "Risk", "Vulnerability", "Exploit"], "ans": "Vulnerability"},
{"q": "Purchasing cyber insurance is an example of which risk strategy?",
 "opts": ["Avoidance", "Mitigation", "Acceptance", "Transference"], "ans": "Transference"},
{"q": "Granting users only the minimum access rights necessary.",
 "opts": ["Separation of Duties", "Defense in Depth", "Least Privilege", "Implicit Deny"], "ans": "Least Privilege"},
{"q": "First phase in the standard Incident Response Lifecycle.",
 "opts": ["Analysis", "Preparation", "Containment", "Post-Incident"], "ans": "Preparation"},
{"q": "Disaster recovery facility fully equipped and ready to take over immediately.",
 "opts": ["Cold Site", "Warm Site", "Hot Site", "Mobile Site"], "ans": "Hot Site"},
{"q": "The maximum acceptable amount of data loss measured in time.", "opts": ["RTO", "MTTR", "RPO", "MTBF"],
 "ans": "RPO"},
{"q": "Biometric verification represents which authentication factor?",
 "opts": ["Knowledge", "Possession", "Inherence", "Behavior"], "ans": "Inherence"},
{"q": "True Multi-Factor Authentication (MFA) requires what?",
 "opts": ["Different passwords", "Different factor categories", "Tokens", "Biometrics"],
 "ans": "Different factor categories"},
{"q": "Software designed to block access or encrypt files until money is paid.",
 "opts": ["Spyware", "Ransomware", "Rootkit", "Adware"], "ans": "Ransomware"},
{"q": "Attack using a botnet to overwhelm a system's bandwidth.",
 "opts": ["Phishing", "Brute-force", "DDoS", "SQL Injection"], "ans": "DDoS"},
{"q": "Vulnerability allowing attackers to bypass authorization and perform privileged tasks.",
 "opts": ["Insecure Design", "Broken Access Control", "Security Misconfiguration", "SSRF"],
 "ans": "Broken Access Control"},
{"q": "Protecting sensitive data using encryption and disabling caching helps prevent:",
 "opts": ["Cryptographic Failures", "Integrity Failures", "Injection", "Broken Auth"], "ans": "Cryptographic Failures"},
{"q": "Attacks where untrusted data is sent to a code interpreter via form input.",
 "opts": ["Outdated Components", "SSRF", "Injection", "Auth Failures"], "ans": "Injection"},
{"q": "Using security questions for password recovery is an example of:",
 "opts": ["Misconfiguration", "Insecure Design", "Broken Access", "Auth Failures"], "ans": "Insecure Design"},
{"q": "Most common vulnerability resulting from default settings or verbose errors.",
 "opts": ["Logging Failures", "Integrity Failures", "Crypto Failures", "Security Misconfiguration"],
 "ans": "Security Misconfiguration"},
{"q": "Attacker finding a security hole in an unpatched third-party library.",
 "opts": ["Vulnerable/Outdated Components", "Insecure Design", "Injection", "SSRF"],
 "ans": "Vulnerable/Outdated Components"},
{"q": "Implementing 2FA and rate limiting helps mitigate:",
 "opts": ["Crypto Failures", "Identification/Auth Failures", "Misconfiguration", "Broken Access"],
 "ans": "Identification/Auth Failures"},
{"q": "Accepting updates without digital signatures or insecure deserialization leads to:",
 "opts": ["Integrity Failures", "SSRF", "Outdated Components", "Crypto Failures"], "ans": "Integrity Failures"},
{"q": "Breaches often go undetected for 200 days. This is a failure in:",
 "opts": ["Auth Failures", "Insecure Design", "Logging/Monitoring", "Integrity Failures"], "ans": "Logging/Monitoring"},
{"q": "Attack causing a server to fetch an unexpected protected resource.", "opts": ["Injection", "SSRF", "XSS", "XEE"],
 "ans": "SSRF"}
]

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TrackAdemia - InfoSec Mastery Quiz")
        self.root.geometry("800x550")
        self.root.config(padx=30, pady=30, bg="#f0f2f5")

        self.score = 0
        self.current_q_index = 0
        random.shuffle(quiz_data)

        self.question_label = tk.Label(root, text="", wraplength=700, font=("Segoe UI", 16, "bold"), bg="#f0f2f5",
                                       fg="#1c1e21")
        self.question_label.pack(pady=(0, 30))

        self.buttons = []
        for i in range(4):
            btn = tk.Button(root, text="", font=("Segoe UI", 12), bg="#ffffff", activebackground="#e4e6eb",
                            relief="flat", height=2, command=lambda i=i: self.check_answer(i))
            btn.pack(pady=8, fill="x")
            self.buttons.append(btn)

        self.feedback_label = tk.Label(root, text="", font=("Segoe UI", 14, "bold"), bg="#f0f2f5")
        self.feedback_label.pack(pady=20)

        self.score_label = tk.Label(root, text=f"Progress: 0 / {len(quiz_data)}  |  Score: 0", font=("Segoe UI", 11),
                                    bg="#f0f2f5", fg="#65676b")
        self.score_label.pack(side="left")

        self.next_btn = tk.Button(root, text="Next Question", font=("Segoe UI", 12, "bold"), bg="#0866ff", fg="white",
                                  state="disabled", padx=20, command=self.next_question)
        self.next_btn.pack(side="right")

        self.load_question()

    def load_question(self):
        self.feedback_label.config(text="")
        self.next_btn.config(state="disabled", bg="#ccd0d5")

        q_data = quiz_data[self.current_q_index]
        self.question_label.config(text=f"Question {self.current_q_index + 1}: {q_data['q']}")

        options = list(q_data["opts"])
        random.shuffle(options)

        for i in range(4):
            self.buttons[i].config(text=options[i], bg="#ffffff", state="normal", fg="#1c1e21")

    def check_answer(self, idx):
        selected = self.buttons[idx].cget("text")
        correct = quiz_data[self.current_q_index]["ans"]

        for btn in self.buttons:
            btn.config(state="disabled")
            if btn.cget("text") == correct:
                btn.config(bg="#42b72a", fg="white")  # Green

        if selected == correct:
            self.score += 1
            self.feedback_label.config(text="✓ Correct!", fg="#42b72a")
        else:
            self.buttons[idx].config(bg="#fa3e3e", fg="white")  # Red
            self.feedback_label.config(text=f"✗ Incorrect! The answer was: {correct}", fg="#fa3e3e")

        self.score_label.config(text=f"Progress: {self.current_q_index + 1} / {len(quiz_data)}  |  Score: {self.score}")
        self.next_btn.config(state="normal", bg="#0866ff")

    def next_question(self):
        self.current_q_index += 1
        if self.current_q_index < len(quiz_data):
            self.load_question()
        else:
            messagebox.showinfo("Quiz Complete",
                                f"Thesis Preparation Finished!\nFinal Score: {self.score} / {len(quiz_data)}")
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()