import ttkbootstrap as tb

class CreateSessionTab(tb.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        tb.Label(self, text="Create New Session", font=("Segoe UI", 16)).pack(pady=20)