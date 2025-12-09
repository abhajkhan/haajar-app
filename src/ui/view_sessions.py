import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import DateEntry
from sqlalchemy import desc
from db import SessionLocal
from models import Session, Subject, Faculty
from datetime import date
from constants import TAB_KIOSK_SCANNER

class ViewSessionsTab(tb.Frame):
    def __init__(self, master, on_navigate, current_user=None, **kw):
        super().__init__(master, **kw)
        self.on_navigate = on_navigate
        self.current_user = current_user
        
        # Variables
        self.faculty_var = tb.StringVar()
        self.subject_var = tb.StringVar()
        self.status_var = tb.StringVar(value="All")
        
        self.faculty_map = {} # Name -> ID
        self.subject_map = {} # Title -> ID
        
        self.current_sessions = []

        self.create_widgets()
        self.load_filter_data()
        self.fetch_sessions()

    def create_widgets(self):
        # Filter Frame
        filter_frame = tb.Labelframe(self, text="Filters", padding=10)
        filter_frame.pack(fill=X, padx=10, pady=5)
        
        # Row 0: Date Range & Status
        tb.Label(filter_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.start_date_entry = DateEntry(filter_frame, bootstyle="primary", firstweekday=0, startdate=date.today(), dateformat='%Y-%m-%d')
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        tb.Label(filter_frame, text="End Date:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        self.end_date_entry = DateEntry(filter_frame, bootstyle="primary", firstweekday=0, startdate=date.today(), dateformat='%Y-%m-%d')
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5, sticky=W)

        tb.Label(filter_frame, text="Status:").grid(row=0, column=4, padx=5, pady=5, sticky=W)
        self.status_cb = tb.Combobox(filter_frame, textvariable=self.status_var, values=["All", "Active", "Inactive"], state="readonly", width=10)
        self.status_cb.grid(row=0, column=5, padx=5, pady=5, sticky=W)
        
        # Row 1: Faculty & Subject
        tb.Label(filter_frame, text="Faculty:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.faculty_cb = tb.Combobox(filter_frame, textvariable=self.faculty_var, state="readonly")
        self.faculty_cb.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        
        tb.Label(filter_frame, text="Subject:").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        self.subject_cb = tb.Combobox(filter_frame, textvariable=self.subject_var, state="readonly")
        self.subject_cb.grid(row=1, column=3, padx=5, pady=5, sticky=W)
        
        # Buttons
        btn_frame = tb.Frame(filter_frame)
        btn_frame.grid(row=2, column=0, columnspan=6, pady=10)
        
        tb.Button(btn_frame, text="Filter", bootstyle="primary", command=self.fetch_sessions_filtered).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Reset", bootstyle="secondary", command=self.reset_filters).pack(side=LEFT, padx=5)

        # Table Frame
        table_frame = tb.Frame(self, padding=10)
        table_frame.pack(fill=BOTH, expand=YES)
        
        columns = ("id", "date", "time", "subject", "faculty", "status", "actions")
        self.tree = tb.Treeview(table_frame, columns=columns, show="headings", bootstyle="info")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("time", text="Time")
        self.tree.heading("subject", text="Subject")
        self.tree.heading("faculty", text="Faculty")
        self.tree.heading("status", text="Status")
        self.tree.heading("actions", text="Actions (Right-Click)")
        
        self.tree.column("id", width=50)
        self.tree.column("date", width=100)
        self.tree.column("time", width=100)
        self.tree.column("subject", width=200)
        self.tree.column("faculty", width=150)
        self.tree.column("status", width=100)
        self.tree.column("actions", width=200)
        
        scrollbar = tb.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Bindings
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Context Menu
        self.context_menu = tb.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open Kiosk", command=self.open_kiosk_context)
        self.context_menu.add_command(label="Mark Inactive", command=self.mark_inactive_context)

    def load_filter_data(self):
        session = SessionLocal()
        try:
            faculties = session.query(Faculty).filter(Faculty.user_id == self.current_user.id).all()
            subjects = session.query(Subject).filter(Subject.user_id == self.current_user.id).all()
            
            self.faculty_map = {f.name: f.id for f in faculties}
            self.subject_map = {s.title: s.id for s in subjects}
            
            self.faculty_cb['values'] = list(self.faculty_map.keys())
            self.subject_cb['values'] = list(self.subject_map.keys())
        finally:
            session.close()

    def fetch_sessions(self, filters=None):
        session = SessionLocal()
        try:
            query = session.query(Session).filter(Session.user_id == self.current_user.id).join(Subject).join(Faculty).order_by(desc(Session.date), desc(Session.start_time))
            
            if filters:
                if 'start_date' in filters and filters['start_date']:
                    query = query.filter(Session.date >= filters['start_date'])
                if 'end_date' in filters and filters['end_date']:
                    query = query.filter(Session.date <= filters['end_date'])
                if 'status' in filters and filters['status'] != "All":
                    is_active = True if filters['status'] == "Active" else False
                    query = query.filter(Session.is_active == is_active)
                if 'faculty_id' in filters and filters['faculty_id']:
                    query = query.filter(Session.faculty_id == filters['faculty_id'])
                if 'subject_id' in filters and filters['subject_id']:
                    query = query.filter(Session.subject_id == filters['subject_id'])
            
            self.current_sessions = query.all()
            self.populate_table()
        except Exception as e:
            Messagebox.show_error(f"Error fetching sessions: {e}", "Database Error")
        finally:
            session.close()

    def fetch_sessions_filtered(self):
        filters = {}
        
        # DateEntry might return string or date depending on version/usage
        # Assuming it returns string in entry.get()
        s_date = self.start_date_entry.entry.get()
        e_date = self.end_date_entry.entry.get()
        
        if s_date:
            filters['start_date'] = s_date
        if e_date:
            filters['end_date'] = e_date
            
        filters['status'] = self.status_var.get()
            
        f_name = self.faculty_var.get()
        if f_name in self.faculty_map:
            filters['faculty_id'] = self.faculty_map[f_name]
            
        s_title = self.subject_var.get()
        if s_title in self.subject_map:
            filters['subject_id'] = self.subject_map[s_title]
            
        self.fetch_sessions(filters)

    def reset_filters(self):
        self.faculty_var.set("")
        self.subject_var.set("")
        self.status_var.set("All")
        self.fetch_sessions()

    def populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for sess in self.current_sessions:
            status = "Active" if sess.is_active else "Inactive"
            actions = "Right-click for options"
            
            values = (
                sess.id,
                sess.date,
                sess.start_time,
                sess.subject.title if sess.subject else "Unknown",
                sess.faculty.name if sess.faculty else "Unknown",
                status,
                actions
            )
            self.tree.insert("", END, values=values)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        self.open_kiosk_context()

    def get_selected_session(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return None
        
        item = self.tree.item(selected_item)
        session_id = item['values'][0]
        
        # Find session object
        for sess in self.current_sessions:
            if sess.id == session_id:
                return sess
        return None

    def open_kiosk_context(self):
        sess = self.get_selected_session()
        if sess:
            if not sess.is_active:
                Messagebox.show_warning("This session is inactive. You can view it but scanning might be disabled.", "Inactive Session")
            # Navigate to Kiosk
            # We need to pass the session object. 
            # The on_navigate callback in MainAppFrame needs to handle (TAB_NAME, session_data) or we pass it differently.
            # For now, let's assume on_navigate can take extra args or we call a specific method.
            # But MainAppFrame.switch_tab only takes tab_name.
            # I will modify MainAppFrame to handle this.
            self.on_navigate(TAB_KIOSK_SCANNER, session_row=sess)

    def mark_inactive_context(self):
        sess = self.get_selected_session()
        if sess:
            if not sess.is_active:
                Messagebox.show_info("Session is already inactive.", "Info")
                return
            
            if Messagebox.yesno(f"Are you sure you want to mark session {sess.id} as Inactive?", "Confirm"):
                self.update_session_status(sess.id, False)

    def update_session_status(self, session_id, is_active):
        session = SessionLocal()
        try:
            sess = session.query(Session).get(session_id)
            if sess:
                sess.is_active = is_active
                session.commit()
                Messagebox.show_info(f"Session {session_id} marked as {'Active' if is_active else 'Inactive'}", "Success")
                self.fetch_sessions_filtered() # Refresh table
        except Exception as e:
            session.rollback()
            Messagebox.show_error(f"Error updating session: {e}", "Database Error")
        finally:
            session.close()
