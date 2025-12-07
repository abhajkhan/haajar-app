import ttkbootstrap as tb
from ttkbootstrap.constants import *
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import func, desc
from db import engine
from models import Student, Faculty, Session
from constants import TAB_CREATE_SESSION

class HomePage(tb.Frame):
    def __init__(self, master, on_navigate, **kw):
        super().__init__(master, **kw)
        self.on_navigate = on_navigate
        
        # Main container with padding
        self.main_container = tb.Frame(self, padding=30)
        self.main_container.pack(fill=BOTH, expand=YES)

        # Header
        self.create_header()
        
        # Stats Section
        self.create_stats_section()
        
        # CTA Section
        self.create_cta_section()

        # Recent Activity
        self.create_recent_activity_section()

    def create_header(self):
        header_frame = tb.Frame(self.main_container)
        header_frame.pack(fill=X, pady=(0, 30))
        
        title = tb.Label(
            header_frame, 
            text="Welcome to Haajar Lab Registry", 
            font=("Segoe UI", 24, "bold"),
            bootstyle="primary"
        )
        title.pack(side=LEFT)
        
        subtitle = tb.Label(
            header_frame,
            text="Manage sessions, attendance, and reports efficiently.",
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        subtitle.pack(side=LEFT, padx=20, pady=(10, 0))

    def create_stats_section(self):
        stats_frame = tb.Labelframe(self.main_container, text="System Overview", padding=20, bootstyle="info")
        stats_frame.pack(fill=X, pady=(0, 30))
        
        # Fetch counts
        student_count = 0
        faculty_count = 0
        session_count = 0
        
        try:
            with SQLSession(engine) as db:
                student_count = db.query(func.count(Student.id)).scalar()
                faculty_count = db.query(func.count(Faculty.id)).scalar()
                session_count = db.query(func.count(Session.id)).scalar()
        except Exception as e:
            print(f"Error fetching stats: {e}")

        # Grid for cards
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)

        self.create_stat_card(stats_frame, "Total Students", str(student_count), "users", 0)
        self.create_stat_card(stats_frame, "Faculty Members", str(faculty_count), "person-badge", 1)
        self.create_stat_card(stats_frame, "Total Sessions", str(session_count), "calendar-check", 2)

    def create_stat_card(self, parent, title, value, icon, col):
        card = tb.Frame(parent, padding=15)
        card.grid(row=0, column=col, sticky=EW, padx=10)
        
        # Value
        tb.Label(
            card, 
            text=value, 
            font=("Segoe UI", 28, "bold"), 
            bootstyle="primary"
        ).pack(anchor=W)
        
        # Title
        tb.Label(
            card, 
            text=title, 
            font=("Segoe UI", 12), 
            bootstyle="secondary"
        ).pack(anchor=W)

    def create_cta_section(self):
        cta_frame = tb.Frame(self.main_container)
        cta_frame.pack(fill=X, pady=(0, 30))
        
        btn = tb.Button(
            cta_frame,
            text="Create New Session",
            bootstyle="success",
            width=25,
            command=lambda: self.on_navigate(TAB_CREATE_SESSION)
        )
        btn.pack(side=LEFT, ipady=10)
        
        help_text = tb.Label(
            cta_frame,
            text="Start a new attendance session for a lab or lecture.",
            bootstyle="secondary",
            font=("Segoe UI", 10, "italic")
        )
        help_text.pack(side=LEFT, padx=20)

    def create_recent_activity_section(self):
        activity_frame = tb.Labelframe(self.main_container, text="Recent Sessions", padding=15, bootstyle="default")
        activity_frame.pack(fill=BOTH, expand=YES)

        columns = ("date", "subject", "faculty", "status")
        tree = tb.Treeview(
            activity_frame, 
            columns=columns, 
            show="headings", 
            bootstyle="primary",
            height=5
        )
        
        tree.heading("date", text="Date")
        tree.heading("subject", text="Subject")
        tree.heading("faculty", text="Faculty")
        tree.heading("status", text="Status")
        
        tree.column("date", width=100)
        tree.column("subject", width=200)
        tree.column("faculty", width=150)
        tree.column("status", width=100)
        
        tree.pack(fill=BOTH, expand=YES)

        # Fetch recent sessions
        try:
            with SQLSession(engine) as db:
                recent_sessions = db.query(Session).order_by(desc(Session.date), desc(Session.start_time)).limit(5).all()
                
                for s in recent_sessions:
                    status = "Active" if s.is_active else "Completed"
                    subject_name = s.subject.title if s.subject else "Unknown"
                    faculty_name = s.faculty.name if s.faculty else "Unknown"
                    tree.insert("", END, values=(s.date, subject_name, faculty_name, status))
        except Exception as e:
            print(f"Error fetching recent sessions: {e}")
