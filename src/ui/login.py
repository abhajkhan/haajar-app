import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from db import SessionLocal
from models import User

class LoginFrame(tb.Frame):
    def __init__(self, master, redirect_to_home, **kw):
        super().__init__(master, **kw)
        self.redirect_to_home = redirect_to_home

        # --- Title ---
        tb.Label(self, text="Department Login", font=("Segoe UI", 18)).pack(pady=20)

        # --- Email Entry ---
        self.email_entry = tb.Entry(self, width=30)
        self.email_entry.pack(pady=10)
        self.email_entry.insert(0, "Email ID")                # simple placeholder
        self.email_entry.bind("<FocusIn>", lambda e: self.email_entry.delete(0, END) 
                        if self.email_entry.get()=="Email ID" else None)

        # --- Password Entry ---
        self.password_entry = tb.Entry(self, width=30, show="")
        self.password_entry.pack(pady=10)
        self.password_entry.insert(0, "Password")             # placeholder
        self.password_entry.bind("<FocusIn>", 
            lambda e: (self.password_entry.delete(0, END), self.password_entry.config(show="*"))
                    if self.password_entry.get()=="Password" else None)

        # --- Login Button ---
        tb.Button(self, text="Login", bootstyle=PRIMARY, command=self.handle_login).pack(pady=20)

    def handle_login(self):
        email = self.email_entry.get().strip()
        pwd = self.password_entry.get().strip()
        
        if not email or email == "Email ID":
            Messagebox.show_error("Please enter your email.", "Validation Error")
            return
        if not pwd or pwd == "Password":
            Messagebox.show_error("Please enter your password.", "Validation Error")
            return

        session = SessionLocal()
        try:
            # Simple plain text password check as per plan
            user = session.query(User).filter(User.department_email == email, User.password == pwd).first()
            
            if user:
                # Login success
                self.redirect_to_home(user)
            else:
                Messagebox.show_error("Invalid email or password.", "Login Failed")
        except Exception as e:
            Messagebox.show_error(f"Database error: {e}", "Error")
        finally:
            session.close()
