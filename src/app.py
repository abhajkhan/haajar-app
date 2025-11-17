from ttkbootstrap import Window
from ui.login import LoginFrame
from ui.main_app_frame import MainAppFrame

def main():
    app = Window(title="Haajar Lab Registry", themename="superhero", size=(1024, 720))

    def switch_to_main():
        login_frame.pack_forget()
        main_frame.pack(fill="both", expand=True)

    login_frame = LoginFrame(app, switch_to_main)
    login_frame.pack(fill="both", expand=True)

    main_frame = MainAppFrame(app)

    app.mainloop()

if __name__ == "__main__":
    main()