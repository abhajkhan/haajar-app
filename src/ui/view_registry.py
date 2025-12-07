import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import DateEntry
from tkinter import filedialog
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from sqlalchemy import desc
from db import SessionLocal
from models import Registry, Session, Student, Subject, Faculty
from datetime import date

class ViewRegistryTab(tb.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        
        # Variables
        self.faculty_var = tb.StringVar()
        self.subject_var = tb.StringVar()
        
        self.faculty_map = {} # Name -> ID
        self.subject_map = {} # Title -> ID
        
        self.current_records = []

        self.create_widgets()
        self.load_filter_data()
        self.fetch_records() # Load default (latest session)

    def create_widgets(self):
        # Filter Frame
        filter_frame = tb.Labelframe(self, text="Filters", padding=10)
        filter_frame.pack(fill=X, padx=10, pady=5)
        
        # Grid layout for filters
        # Row 0: Date Range
        tb.Label(filter_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.start_date_entry = DateEntry(filter_frame, bootstyle="primary", firstweekday=0, startdate=date.today(), dateformat='%Y-%m-%d')
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        tb.Label(filter_frame, text="End Date:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        self.end_date_entry = DateEntry(filter_frame, bootstyle="primary", firstweekday=0, startdate=date.today(), dateformat='%Y-%m-%d')
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5, sticky=W)
        
        # Row 1: Faculty & Subject
        tb.Label(filter_frame, text="Faculty:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.faculty_cb = tb.Combobox(filter_frame, textvariable=self.faculty_var, state="readonly")
        self.faculty_cb.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        
        tb.Label(filter_frame, text="Subject:").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        self.subject_cb = tb.Combobox(filter_frame, textvariable=self.subject_var, state="readonly")
        self.subject_cb.grid(row=1, column=3, padx=5, pady=5, sticky=W)
        
        # Buttons
        btn_frame = tb.Frame(filter_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        tb.Button(btn_frame, text="Filter", bootstyle="primary", command=self.fetch_records_filtered).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Reset", bootstyle="secondary", command=self.reset_filters).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Export Excel", bootstyle="success", command=self.export_excel).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Export PDF", bootstyle="danger", command=self.export_pdf).pack(side=LEFT, padx=5)

        # Table Frame
        table_frame = tb.Frame(self, padding=10)
        table_frame.pack(fill=BOTH, expand=YES)
        
        columns = ("date", "time", "student_name", "roll_no", "subject", "faculty", "status")
        self.tree = tb.Treeview(table_frame, columns=columns, show="headings", bootstyle="info")
        
        self.tree.heading("date", text="Date")
        self.tree.heading("time", text="Time")
        self.tree.heading("student_name", text="Student Name")
        self.tree.heading("roll_no", text="Roll No")
        self.tree.heading("subject", text="Subject")
        self.tree.heading("faculty", text="Faculty")
        self.tree.heading("status", text="Status")
        
        self.tree.column("date", width=100)
        self.tree.column("time", width=100)
        self.tree.column("student_name", width=200)
        self.tree.column("roll_no", width=100)
        self.tree.column("subject", width=150)
        self.tree.column("faculty", width=150)
        self.tree.column("status", width=150)
        
        scrollbar = tb.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

    def load_filter_data(self):
        session = SessionLocal()
        try:
            faculties = session.query(Faculty).all()
            subjects = session.query(Subject).all()
            
            self.faculty_map = {f.name: f.id for f in faculties}
            self.subject_map = {s.title: s.id for s in subjects}
            
            self.faculty_cb['values'] = list(self.faculty_map.keys())
            self.subject_cb['values'] = list(self.subject_map.keys())
        finally:
            session.close()

    def fetch_records(self, filters=None):
        session = SessionLocal()
        try:
            query = session.query(Registry, Session, Student, Subject, Faculty)\
                .join(Session, Registry.session_id == Session.id)\
                .join(Student, Registry.student_id == Student.id)\
                .join(Subject, Session.subject_id == Subject.id)\
                .join(Faculty, Session.faculty_id == Faculty.id)
            
            if filters:
                if 'start_date' in filters and filters['start_date']:
                    query = query.filter(Session.date >= filters['start_date'])
                if 'end_date' in filters and filters['end_date']:
                    query = query.filter(Session.date <= filters['end_date'])
                if 'faculty_id' in filters and filters['faculty_id']:
                    query = query.filter(Session.faculty_id == filters['faculty_id'])
                if 'subject_id' in filters and filters['subject_id']:
                    query = query.filter(Session.subject_id == filters['subject_id'])
            else:
                # Default: Most recent session
                # Find the most recent session ID
                subq = session.query(Session.id).order_by(desc(Session.date), desc(Session.start_time)).limit(1).scalar_subquery()
                # If no sessions exist, subq might be None, handle gracefully
                # But scalar_subquery returns a query object, not result.
                
                # Let's try a different approach for default: get the latest session object first
                latest_session = session.query(Session).order_by(desc(Session.date), desc(Session.start_time)).first()
                if latest_session:
                    query = query.filter(Session.id == latest_session.id)
                else:
                    # No sessions, return empty
                    query = query.filter(Session.id == -1)

            records = query.all()
            self.populate_table(records)
        except Exception as e:
            Messagebox.show_error(f"Error fetching records: {e}", "Database Error")
        finally:
            session.close()

    def fetch_records_filtered(self):
        filters = {}
        
        s_date = self.start_date_entry.entry.get()
        e_date = self.end_date_entry.entry.get()
        
        if s_date:
            filters['start_date'] = s_date
        if e_date:
            filters['end_date'] = e_date
            
        f_name = self.faculty_var.get()
        if f_name in self.faculty_map:
            filters['faculty_id'] = self.faculty_map[f_name]
            
        s_title = self.subject_var.get()
        if s_title in self.subject_map:
            filters['subject_id'] = self.subject_map[s_title]
            
        self.fetch_records(filters)

    def reset_filters(self):
        self.faculty_var.set("")
        self.subject_var.set("")
        # Reset dates to today or clear? Let's keep today as default or clear.
        # DateEntry doesn't have a clear method easily, but we can set it.
        # Let's just reset to default view (latest session)
        self.fetch_records()

    def populate_table(self, records):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.current_records = []
        
        for reg, sess, stu, sub, fac in records:
            status = "Late" if reg.late_check_in_reason else "On Time"
            
            values = (
                sess.date,
                reg.check_in_time,
                stu.name,
                stu.roll_no,
                sub.title,
                fac.name,
                status
            )
            self.tree.insert("", END, values=values)
            
            self.current_records.append({
                "Date": sess.date,
                "Time": reg.check_in_time,
                "Student Name": stu.name,
                "Roll No": stu.roll_no,
                "Subject": sub.title,
                "Faculty": fac.name,
                "Status": status
            })

    def export_excel(self):
        if not self.current_records:
            Messagebox.show_warning("No records to export", "Export Warning")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                df = pd.DataFrame(self.current_records)
                df.to_excel(file_path, index=False)
                Messagebox.show_info("Export Successful", "Export")
            except Exception as e:
                Messagebox.show_error(f"Export failed: {e}", "Export Error")

    def export_pdf(self):
        if not self.current_records:
            Messagebox.show_warning("No records to export", "Export Warning")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            try:
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                elements = []
                
                data = [["Date", "Time", "Student Name", "Roll No", "Subject", "Faculty", "Status"]]
                for rec in self.current_records:
                    data.append([
                        str(rec["Date"]),
                        str(rec["Time"]),
                        rec["Student Name"],
                        rec["Roll No"],
                        rec["Subject"],
                        rec["Faculty"],
                        rec["Status"]
                    ])
                    
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
                doc.build(elements)
                Messagebox.show_info("Export Successful", "Export")
            except Exception as e:
                Messagebox.show_error(f"Export failed: {e}", "Export Error")