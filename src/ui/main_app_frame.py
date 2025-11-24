import ttkbootstrap as tb
from ui.sidebar import Sidebar
from ui.view_registry import ViewRegistryTab
from ui.create_session import CreateSessionTab
from ui.kiosk_scanner import KioskScanner
from constants import *

class MainAppFrame(tb.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.sidebar = Sidebar(self, self.switch_tab)
        self.content_area = tb.Frame(self)
        self.content_area.pack(side="right", expand=True, fill="both")

        self.tabs = {
            TAB_CREATE_SESSION: CreateSessionTab(self.content_area),
            TAB_VIEW_REGISTRY: ViewRegistryTab(self.content_area),
            # kiosk_scanner tab created lazily when session is created
        }

        self.active_tab = None

    def _on_session_created(self, session_row):
        """
        Called by CreateSessionTab after the session is saved in DB.
        Create kiosk scanner tab (or replace it) and switch to it.
        """
        # create or replace kiosk tab
        kiosk = KioskScanner(self.content_area, session_row=session_row)
        self.tabs[TAB_KIOSK_SCANNER] = kiosk
        # switch
        self.switch_tab(TAB_KIOSK_SCANNER)

    def switch_tab(self, tab_name):
        if self.active_tab:
            try:
                # if kiosk scanner, ensure it stops camera when hidden
                if isinstance(self.active_tab, KioskScanner):
                    self.active_tab.stop()
            except Exception:
                pass
            self.active_tab.pack_forget()
        self.active_tab = self.tabs[tab_name]
        self.active_tab.pack(fill="both", expand=True)
