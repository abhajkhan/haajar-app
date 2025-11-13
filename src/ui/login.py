import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk

class LoginFrame(tb.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        lbl = tb.Label(self, text="Department Login", font=("Segoe UI", 18))
        lbl.pack(pady=20)
        self.email = tb.Entry(self)
        self.email.pack(pady=5)
        self.pw = tb.Entry(self, show="*")
        self.pw.pack(pady=5)
        tb.Button(self, text="Login", command=self.handle_login).pack(pady=10)
    def handle_login(self):
        # authenticate against user_account
        pass
