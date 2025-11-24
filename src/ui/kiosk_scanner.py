# src/ui/kiosk_scanner.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from threading import Thread, Event
from datetime import datetime
import time

# cv / barcode libs
import cv2
from pyzbar import pyzbar
from PIL import Image, ImageTk

# DB imports - adjust names to your project
try:
    from db import SessionLocal
    from models import Registry as RegistryModel, Student as StudentModel, Session as SessionModel
except Exception:
    from ..db import SessionLocal
    from ..models import Registry as RegistryModel, Student as StudentModel, Session as SessionModel

class KioskScanner(tb.Frame):
    """
    Kiosk scanner UI. Accepts session_id when opened.
    Starts camera automatically and listens for QR/barcode scans.
    When a code is decoded it looks up the Student (by encoded student_id/roll) and
    creates or updates a Registry row (check-in/check-out).
    """
    def __init__(self, master, session_row=None, **kw):
        super().__init__(master, **kw)
        self.session_row = session_row
        self._stop_event = Event()
        self.cap = None
        self.reader_thread = None

        tb.Label(self, text="Kiosk Scanner", font=("Segoe UI", 16)).pack(pady=8)
        info = tb.Label(self, text=f"Session: {getattr(session_row, 'id', 'N/A')}  Subject: {getattr(getattr(session_row, 'subject', None), 'title', '')}")
        info.pack()

        # video display
        self.video_label = tb.Label(self)
        self.video_label.pack(padx=8, pady=8)

        # status
        self.status = tb.Label(self, text="Initializing camera...", bootstyle="warning")
        self.status.pack(pady=(0,8))

        # control buttons
        btns = tb.Frame(self)
        btns.pack(fill="x", padx=8, pady=6)
        tb.Button(btns, text="Stop Scanner", bootstyle="danger", command=self.stop).pack(side="right")
        tb.Button(btns, text="Manual Sync (DB)", bootstyle="secondary", command=self._manual_sync).pack(side="left")

        # start camera thread
        self._start_camera()

    def _manual_sync(self):
        messagebox.showinfo("Info", "Manual sync placeholder. Implement offline sync logic here.")

    def _start_camera(self):
        self._stop_event.clear()
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # remove backend flag on linux if needed
            if not self.cap or not self.cap.isOpened():
                # try without flag
                self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.status.config(text="Failed to open camera.", bootstyle="danger")
                return
            self.status.config(text="Camera opened. Scanning...", bootstyle="success")
            self.reader_thread = Thread(target=self._camera_loop, daemon=True)
            self.reader_thread.start()
        except Exception as e:
            self.status.config(text=f"Camera error: {e}", bootstyle="danger")

    def _camera_loop(self):
        while not self._stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # resize for display
            h, w = frame.shape[:2]
            scale = 640 / max(w, h)
            frame_disp = cv2.resize(frame, (int(w*scale), int(h*scale)))

            # convert to PIL for tkinter
            cv2image = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=pil)
            # keep a reference
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # decode barcodes/QRs
            codes = pyzbar.decode(frame)
            if codes:
                for code in codes:
                    try:
                        data = code.data.decode("utf-8")
                    except Exception:
                        data = None
                    if data:
                        # we assume QR encodes a student identifier (roll or ID)
                        self._handle_scan(data)
                        # brief pause after successful read to avoid duplicates
                        time.sleep(1.2)
            # small sleep so UI remains responsive
            time.sleep(0.02)

        # release camera on exit
        try:
            self.cap.release()
        except Exception:
            pass
        self.video_label.config(image="")

    def _handle_scan(self, data):
        """
        Handle the scanned payload. Data format expectation:
        - simplest: student id (integer) OR student roll string
        You can change parsing logic to e.g. JSON payloads later.
        """
        db = SessionLocal()
        try:
            # try find student by numeric id first, then by roll or admission no
            student = None
            if data.isdigit():
                student = db.query(StudentModel).filter(StudentModel.id == int(data)).first()
            if student is None:
                # try by rollno or admission no or name
                student = db.query(StudentModel).filter(
                    (StudentModel.roll_no == data) | 
                    (StudentModel.admission_no == data) |
                    (StudentModel.name == data)
                ).first()

            if student is None:
                # no matching student, show message
                self.status.config(text=f"Unknown QR payload: {data}", bootstyle="warning")
                return

            # find registry entry for this session + student where check_out_time is null
            reg = db.query(RegistryModel).filter(
                RegistryModel.session_id == self.session_row.id,
                RegistryModel.student_id == student.id,
            ).order_by(RegistryModel.id.desc()).first()

            now = datetime.now()

            if reg is None or (reg and reg.check_out_time is not None):
                # create check-in
                new_reg = RegistryModel(
                    student_id=student.id,
                    session_id=self.session_row.id,
                    check_in_time=now,
                    check_out_time=None
                )
                db.add(new_reg)
                db.commit()
                db.refresh(new_reg)
                self.status.config(text=f"Checked IN: {student.name}", bootstyle="success")
            else:
                # existing open check-in -> close it (check-out)
                reg.check_out_time = now
                db.add(reg)
                db.commit()
                self.status.config(text=f"Checked OUT: {student.name}", bootstyle="info")
        except Exception as e:
            db.rollback()
            self.status.config(text=f"DB error: {e}", bootstyle="danger")
        finally:
            db.close()

    def stop(self):
        """Stop camera & thread"""
        self._stop_event.set()
        # ensure capture released
        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except Exception:
                pass
        self.status.config(text="Scanner stopped.", bootstyle="secondary")
