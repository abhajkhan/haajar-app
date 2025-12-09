import ttkbootstrap as tb
from constants import TABS

class Sidebar(tb.Frame):
    def __init__(self, master, on_nav_click, **kw):
        super().__init__(master, bootstyle="dark", width=300, **kw)
        self.pack(side="left", fill="y")
        self.pack_propagate(False)

        tb.Label(self, text="Menu", bootstyle="inverse-dark", font=("Segoe UI", 14)).pack(pady=10)

        for label in TABS.values():
            tb.Button(self, text=label, bootstyle="primary", command=lambda n=label: on_nav_click(n)).pack(fill="x", padx=10, pady=5)