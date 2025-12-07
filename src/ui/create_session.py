import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime, date, time, timedelta

try:
    from db import SessionLocal
    from models import Session as SessionModel, Subject as SubjectModel, Faculty as FacultyModel
except Exception as e:
    print("!!Exception in importing SessionLocal from db.py", e)

class CreateSessionTab(tb.Frame):
    def __init__(self, master, on_create=None, current_user=None, **kw):
        """
        subjects: optional list of subject titles (strings) — used for Combobox.
        faculties: optional list of faculty names.
        on_create: callback(session_row) called when session saved to DB successfully.
        """
        super().__init__(master, **kw)
        self.on_create = on_create
        self.current_user = current_user

        try:
            db = SessionLocal()
            # Filter by current user
            self.subjects = db.query(SubjectModel).filter(SubjectModel.user_id == self.current_user.id).all() or []
            self.faculties = db.query(FacultyModel).filter(FacultyModel.user_id == self.current_user.id).all() or []
        except Exception as e:
            print("Exception in fetching sub and fac: ",e)
            self.subjects = []
            self.faculties = []
        finally:
            db.close()

        tb.Label(self, text="Create New Session", font=("Segoe UI", 16, "bold"), bootstyle="primary").pack(pady=(12, 8))

        form = tb.Frame(self)
        form.pack(padx=16, pady=8, fill="x", expand=True)

        # Subject
        tb.Label(form, text="Subject").grid(row=0, column=0, sticky="w", pady=6)
        self.subject_cb = tb.Combobox(form, values=[subject.title for subject in self.subjects], bootstyle="info", state="readonly")
        self.subject_cb.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        if self.subjects:
            self.subject_cb.set(self.subjects[0].title)

        # Faculty
        tb.Label(form, text="Faculty").grid(row=1, column=0, sticky="w", pady=6)
        self.faculty_cb = tb.Combobox(form, values=[fac.name for fac in self.faculties], bootstyle="info", state="readonly")
        self.faculty_cb.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        if self.faculties:
            self.faculty_cb.set(self.faculties[0].name)

        # Date
        tb.Label(form, text="Date").grid(row=2, column=0, sticky="w", pady=6)
        try:
            self.date_entry = tb.DateEntry(form, bootstyle="secondary")
        except Exception:
            from datetime import date as _d
            self.date_entry = tb.Entry(form)
            self.date_entry.insert(0, _d.today().isoformat())
        self.date_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        # Start time (HH:MM)
        tb.Label(form, text="Start Time (HH:MM)").grid(row=3, column=0, sticky="w", pady=6)
        start_frame = tb.Frame(form); start_frame.grid(row=3, column=1, sticky="w", padx=8, pady=6)
        self.start_hour = tb.Spinbox(start_frame, from_=0, to=23, width=4, format="%02.0f"); self.start_hour.pack(side="left")
        tb.Label(start_frame, text=":").pack(side="left")
        self.start_min = tb.Spinbox(start_frame, from_=0, to=59, width=4, format="%02.0f"); self.start_min.pack(side="left")

        # End time (HH:MM)
        tb.Label(form, text="End Time (HH:MM)").grid(row=4, column=0, sticky="w", pady=6)
        end_frame = tb.Frame(form); end_frame.grid(row=4, column=1, sticky="w", padx=8, pady=6)
        self.end_hour = tb.Spinbox(end_frame, from_=0, to=23, width=4, format="%02.0f"); self.end_hour.pack(side="left")
        tb.Label(end_frame, text=":").pack(side="left")
        self.end_min = tb.Spinbox(end_frame, from_=0, to=59, width=4, format="%02.0f"); self.end_min.pack(side="left")

        # Remarks
        tb.Label(form, text="Remarks").grid(row=5, column=0, sticky="nw", pady=6)
        self.remarks = tb.Text(form, height=4, width=30)
        self.remarks.grid(row=5, column=1, sticky="ew", padx=8, pady=6)

        # Buttons
        buttons = tb.Frame(self); buttons.pack(fill="x", padx=16, pady=(6,12))
        create_btn = tb.Button(buttons, text="Create Session", bootstyle="success", command=self._on_create_clicked)
        create_btn.pack(side="right", padx=(8, 0))
        tb.Button(buttons, text="Clear", bootstyle="secondary", command=self.clear_form).pack(side="right")

        # grid weights for responsive layout
        form.columnconfigure(1, weight=1)

    def clear_form(self):
        if self.subjects:
            self.subject_cb.set(self.subjects[0].title)
        if self.faculties:
            self.faculty_cb.set(self.faculties[0].name)
        try:
            self.date_entry.set_date(date.today())
        except Exception:
            self.date_entry.delete(0, "end"); self.date_entry.insert(0, date.today().isoformat())
        self.start_hour.delete(0, "end"); self.start_hour.insert(0, "09")
        self.start_min.delete(0, "end"); self.start_min.insert(0, "00")
        self.end_hour.delete(0, "end"); self.end_hour.insert(0, "09")
        self.end_min.delete(0, "end"); self.end_min.insert(0, "00")
        self.remarks.delete("1.0", "end")

    def _get_date_value(self):
        try:
            return self.date_entry.get_date()
        except Exception:
            txt = self.date_entry.get().strip()
            try:
                return datetime.strptime(txt, "%Y-%m-%d").date()
            except Exception:
                return None

    def _safe_int(self, v, default=0):
        try:
            return int(str(v).strip())
        except Exception:
            return default

    def _on_create_clicked(self):
        subject_title = self.subject_cb.get().strip()
        faculty_name = self.faculty_cb.get().strip()
        d = self._get_date_value()
        start_h = self._safe_int(self.start_hour.get())
        start_m = self._safe_int(self.start_min.get())
        end_h = self._safe_int(self.end_hour.get())
        end_m = self._safe_int(self.end_min.get())
        remarks = self.remarks.get("1.0", "end").strip()

        if not subject_title:
            messagebox.showwarning("Validation", "Choose a subject.")
            return
        if not faculty_name:
            messagebox.showwarning("Validation", "Choose a faculty.")
            return
        if d is None:
            messagebox.showwarning("Validation", "Enter a valid date (YYYY-MM-DD).")
            return
        if not (datetime.now().hour <= start_h <= 23 and 0 <= start_m <= 59):
            messagebox.showwarning("Validation", "Enter valid start time.")
            return
        if not (start_h <= end_h <= 23 and 0 <= end_m <= 59):
            messagebox.showwarning("Validation", "Enter valid end time.")
            return
        

        start_dt = datetime.combine(d, time(hour=start_h, minute=start_m))
        end_dt = datetime.combine(d, time(hour=end_h, minute=end_m))

        # persist to DB
        db = SessionLocal()
        try:
            # find subject by title
            subj = db.query(SubjectModel).filter(SubjectModel.title == subject_title).first()
            if subj is None:
                messagebox.showerror("DB", f"Subject '{subject_title}' not found in DB.")
                return

            fac = db.query(FacultyModel).filter(FacultyModel.name == faculty_name).first()
            if fac is None:
                messagebox.showerror("DB", f"Faculty '{faculty_name}' not found in DB.")
                return

            new_session = SessionModel(
                subject_id=subj.id,
                faculty_id=fac.id,
                date=d,
                start_time=start_dt.time(),
                end_time=end_dt.time(),
                is_active=True,
                remarks=remarks,
                user_id=self.current_user.id
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)

            # success: inform user and call callback to switch to kiosk scanner
            messagebox.showinfo("Success", f"Session created (id={new_session.id}). Switching to kiosk scanner.")
            # callback receives the created DB model (or id)
            if callable(self.on_create):
                try:
                    self.on_create(new_session)  # main app will use this to open kiosk
                except Exception as cb_e:
                    messagebox.showerror("Callback error", str(cb_e))
        except Exception as e:
            db.rollback()
            messagebox.showerror("DB error", str(e))
        finally:
            db.close()
