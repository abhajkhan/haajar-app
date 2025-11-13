import ttkbootstrap as tb
from ui.login import LoginFrame

def main():
    app = tb.Window(title="Haajar Lab Registry", themename="superhero", size=(1024, 720))
    LoginFrame(app).pack(fill="both", expand=True)
    app.mainloop()

if __name__ == "__main__":
    main()
