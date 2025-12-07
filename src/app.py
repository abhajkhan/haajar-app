from ttkbootstrap import Window
from ui.login import LoginFrame
from ui.main_app_frame import MainAppFrame
from db import Base, engine
import models

def main():
    print("Checking & creating tables if needed...")
    Base.metadata.create_all(engine)
    print("Database Ready!")

    app = Window(title="Haajar Lab Registry", themename="superhero", size=(1024, 720))

    def redirect_to_home(user):
        login_frame.pack_forget()
        main_frame = MainAppFrame(app, current_user=user)
        main_frame.pack(fill="both", expand=True)

    login_frame = LoginFrame(app, redirect_to_home)
    login_frame.pack(fill="both", expand=True)

    app.mainloop()


if __name__ == "__main__":
    main()
