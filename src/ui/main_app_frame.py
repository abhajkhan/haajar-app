import ttkbootstrap as tb
from ui.sidebar import Sidebar
from ui.view_registry import ViewRegistryTab
from ui.create_session import CreateSessionTab
from constants import *

class MainAppFrame(tb.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.sidebar = Sidebar(self, self.switch_tab)
        self.content_area = tb.Frame(self)
        self.content_area.pack(side="right", expand=True, fill="both")

        self.tabs = {
            TAB_CREATE_SESSION: CreateSessionTab(self.content_area,subjects=["Python Lab", "DB Lab", "OS Lab"]),
            TAB_VIEW_REGISTRY: ViewRegistryTab(self.content_area),
        }

        self.active_tab = None

    def switch_tab(self, tab_name):
        if self.active_tab:
            self.active_tab.pack_forget()
        self.active_tab = self.tabs[tab_name]
        self.active_tab.pack(fill="both", expand=True)