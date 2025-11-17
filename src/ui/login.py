import ttkbootstrap as tb

class LoginFrame(tb.Frame):
    def __init__(self, master, switch_to_main, **kw):
        super().__init__(master, **kw)
        self.switch_to_main = switch_to_main

        tb.Label(self, text="Department Login", font=("Segoe UI", 18)).pack(pady=20)
        self.email = tb.Entry(self)
        self.email.pack(pady=5)
        self.pw = tb.Entry(self, show="*")
        self.pw.pack(pady=5)
        tb.Button(self, text="Login", command=self.handle_login).pack(pady=10)

    def handle_login(self):
        # Add authentication logic here
        self.switch_to_main()