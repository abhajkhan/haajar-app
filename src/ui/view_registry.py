import ttkbootstrap as tb

class ViewRegistryTab(tb.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        tb.Label(self, text="Attendance Registry", font=("Segoe UI", 16)).pack(pady=20)