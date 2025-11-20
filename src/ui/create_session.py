import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime, date, time

class CreateSessionTab(tb.Frame):
    def __init__(self, master, subjects=None, faculties=None,on_create=None, **kw):
        """
        subjects: list of subject strings (e.g. ["Python Lab", "DSA"])
        on_create: optional callback(session_dict) when create succeeds
        """
        super().__init__(master, **kw)
        self.on_create = on_create
        self.subjects = subjects or ["MCA - Python Lab", "MCA - DB Lab", "MCA - OS Lab"]
        self.faculties = faculties or ["Foussia", "Nadheera", "Vaheedha"]

        tb.Label(self, text="Create New Session", font=("Segoe UI", 16)).pack(pady=(12, 8))

        form = tb.Frame(self)
        form.pack(padx=16, pady=8, fill="x", expand=True)

        # Subject
        tb.Label(form, text="Subject").grid(row=0, column=0, sticky="w", pady=6)
        self.subject_cb = tb.Combobox(form, values=self.subjects, bootstyle="info", state="readonly")
        self.subject_cb.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        self.subject_cb.set(self.subjects[0])

        # Faculty
        tb.Label(form, text="Faculty").grid(row=1, column=0, sticky="w", pady=6)
        self.faculty_cb = tb.Combobox(form, values=self.faculties, bootstyle="info", state="readonly")
        self.faculty_cb.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        self.faculty_cb.set(self.faculties[0])

        # Date
        tb.Label(form, text="Date").grid(row=2, column=0, sticky="w", pady=6)
        # ttkbootstrap exposes a DateEntry (backed by tkcalendar) if available
        try:
            self.date_entry = tb.DateEntry(form, bootstyle="secondary")
        except Exception:
            # Fallback to simple Entry with YYYY-MM-DD placeholder if DateEntry not available
            self.date_entry = tb.Entry(form)
            self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        # Start time (HH:MM)
        tb.Label(form, text="Start Time (HH:MM)").grid(row=3, column=0, sticky="w", pady=6)
        start_frame = tb.Frame(form)
        start_frame.grid(row=3, column=1, sticky="w", padx=8, pady=6)
        self.start_hour = tb.Spinbox(start_frame, from_=0, to=23, width=4, format="%02.0f")
        self.start_min = tb.Spinbox(start_frame, from_=0, to=59, width=4, format="%02.0f")
        self.start_hour.pack(side="left")
        tb.Label(start_frame, text=":").pack(side="left")
        self.start_min.pack(side="left")

       # End time (HH:MM)
        tb.Label(form, text="End Time (HH:MM)").grid(row=4, column=0, sticky="w", pady=6)
        end_frame = tb.Frame(form)
        end_frame.grid(row=4, column=1, sticky="w", padx=8, pady=6)
        self.end_hour = tb.Spinbox(end_frame, from_=0, to=23, width=4, format="%02.0f")
        self.end_min = tb.Spinbox(end_frame, from_=0, to=59, width=4, format="%02.0f")
        self.end_hour.pack(side="left")
        tb.Label(end_frame, text=":").pack(side="left")
        self.end_min.pack(side="left")

        # Remarks
        tb.Label(form, text="Remarks").grid(row=5, column=0, sticky="nw", pady=6)
        self.remarks = tb.Text(form, height=4, width=30)
        self.remarks.grid(row=5, column=1, sticky="ew", padx=8, pady=6)

        # Buttons
        btn_frame = tb.Frame(self)
        btn_frame.pack(fill="x", padx=16, pady=(6, 12))
        create_btn = tb.Button(btn_frame, text="Create Session", bootstyle="success", command=self.create_session)
        cancel_btn = tb.Button(btn_frame, text="Cancel", bootstyle="secondary", command=self.clear_form)
        create_btn.pack(side="right", padx=(8,0))
        cancel_btn.pack(side="right")

        # grid weights for responsive layout
        form.columnconfigure(1, weight=1)

    def clear_form(self):
        """Reset inputs to defaults"""
        self.subject_cb.set(self.subjects[0])
        try:
            self.date_entry.set_date(date.today())
        except Exception:
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, date.today().isoformat())
        self.start_hour.delete(0, "end"); self.start_hour.insert(0, "09")
        self.start_min.delete(0, "end"); self.start_min.insert(0, "00")
        self.duration_spin.delete(0, "end"); self.duration_spin.insert(0, "1")
        self.remarks.delete("1.0", "end")

    def create_session(self):
        """Validate and emit a session object (replace print with DB call)"""
        subject = self.subject_cb.get().strip()
        faculty = self.faculty_cb.get().strip()
        raw_date = self._get_date_value()
        start_h = self._safe_int(self.start_hour.get())
        start_m = self._safe_int(self.start_min.get())
        end_h = self._safe_int(self.end_hour.get())
        end_m = self._safe_int(self.end_min.get())
    
        remarks = self.remarks.get("1.0", "end").strip()

        # basic validation
        if not subject:
            messagebox.showwarning("Validation", "Please select a subject.")
            return
        if not faculty:
            messagebox.showwarning("Validation", "Please select a Faculty.")
            return
        if raw_date is None:
            messagebox.showwarning("Validation", "Please enter a valid date (YYYY-MM-DD).")
            return
        if not (0 <= start_h <= 23 and 0 <= start_m <= 59):
            messagebox.showwarning("Validation", "Please enter a valid start time.")
            return
        if not (start_h <= end_h <= 23 and 0 <= end_m <= 59):
            messagebox.showwarning("Validation", "Please enter a valid end time.")
            return

        start_dt = datetime.combine(raw_date, time(hour=start_h, minute=start_m))
        end_dt = datetime.combine(raw_date, time(hour=end_h, minute=end_m))
        

        session = {
            "subject": subject,
            "faculty": faculty,
            "date": raw_date.isoformat(),
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "remarks": remarks,
            "is_active": True
        }

        # Placeholder action: print or call provided callback
        print("Created session:", session)
        messagebox.showinfo("Session Created", f"Session for '{subject}' on {raw_date.isoformat()} created.")
        if callable(self.on_create):
            try:
                self.on_create(session)
            except Exception as e:
                # callback failed — show message but don't crash
                messagebox.showerror("Callback error", str(e))

    def _get_date_value(self):
        """Try to parse date from DateEntry or Entry"""
        try:
            # DateEntry has get_date()
            val = self.date_entry.get_date()
            if isinstance(val, date):
                return val
        except Exception:
            pass
        # fallback: parse text yyyy-mm-dd
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

# Demo / standalone usage
if __name__ == "__main__":
    from datetime import timedelta
    root = tb.Window(themename="litera")
    root.title("Lab Session Creator - Demo")
    root.geometry("600x420")

    def on_create_cb(session_obj):
        # example: replace with DB save
        print("on_create_cb received:", session_obj)

    tab = CreateSessionTab(root, subjects=["Python Lab", "DB Lab", "OS Lab"], on_create=on_create_cb)
    tab.pack(fill="both", expand=True)

    root.mainloop()
