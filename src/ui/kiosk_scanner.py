# src/ui/kiosk_scanner.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from threading import Thread, Event
from datetime import datetime, timedelta
import time
import platform
try:
    import winsound  # Windows beep
except Exception:
    winsound = None
try:
    import simpleaudio as sa  # cross-platform small library (optional)
except Exception:
    sa = None

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
    from ..db import SessionLocal
    from ..models import Registry as RegistryModel, Student as StudentModel, Session as SessionModel

from utils.logger import get_logger

class KioskScanner(tb.Frame):
    """
    Kiosk scanner UI. Accepts session_id when opened.
    Starts camera automatically and listens for QR/barcode scans.
    When a code is decoded it looks up the Student (by encoded student_id/roll) and
    creates or updates a Registry row (check-in/check-out).
    """
    def __init__(self, master, session_row=None, **kw):
        super().__init__(master, **kw)
        self.logger = get_logger(self.__class__.__name__)
        self.session_row = session_row
        self._stop_event = Event()
        self.cap = None
        self.reader_thread = None
        self.cv2_detector = cv2.QRCodeDetector() # Initialize cv2 detector
        self.recent_scans = {}         # payload -> last_seen_ts (float)
        self.last_overlay = None       # dict with keys: rect, msg, color, ts, ttl
        self.overlay_ttl = 1.5         # seconds to display overlay after a scan

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
                self.logger.error("Failed to open camera.")
                return
            self.status.config(text="Camera opened. Scanning...", bootstyle="success")
            self.logger.info("Camera opened successfully. Scanning started.")
            self.reader_thread = Thread(target=self._camera_loop, daemon=True)
            self.reader_thread.start()
        except Exception as e:
            self.status.config(text=f"Camera error: {e}", bootstyle="danger")
            self.logger.error(f"Camera error: {e}")

    def _camera_loop(self):
        while not self._stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # Optionally scale frame for display
            h, w = frame.shape[:2]
            scale = 640 / max(w, h)
            frame_disp = cv2.resize(frame, (int(w*scale), int(h*scale)))

            # If there's an overlay to render (set by _handle_scan),
            # draw rectangle and message directly on the frame_disp
            if self.last_overlay:
                now = time.time()
                if now - self.last_overlay["ts"] <= self.last_overlay["ttl"]:
                    r = self.last_overlay.get("rect")
                    msg = self.last_overlay.get("msg", "")
                    color = self.last_overlay.get("color", (0,255,0))  # BGR
                    if r:
                        # scale rect coordinates if needed (assume frame_disp scaled)
                        x, y, w_rect, h_rect = r
                        cv2.rectangle(frame_disp, (x, y), (x + w_rect, y + h_rect), color, 3)
                    # draw message background
                    cv2.rectangle(frame_disp, (8,8), (8+len(msg)*9 + 12, 36), (0,0,0), -1)
                    cv2.putText(frame_disp, msg, (12,28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                else:
                    self.last_overlay = None

            # convert to PIL and update Tk label as before
            cv2image = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=pil)
            # keep a reference to avoid garbage collection
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # Invert frame for better detection
            inverted_frame = cv2.bitwise_not(frame)
            
            # Method 1: pyzbar
            codes = pyzbar.decode(inverted_frame)
            print("QR-Codes: ",codes)
            
            # Method 2: cv2 detector (fallback/parallel)
            if not codes:
                try:
                    data, bbox, _ = self.cv2_detector.detectAndDecode(frame)
                    if data:
                        # Create a dummy object to match pyzbar structure if needed, or just process directly
                        # For simplicity, let's just process it if found
                        self.logger.debug(f"cv2 detected: {data}")
                        self._handle_scan(data, None)

                    # !!!!!!!!!!!!!!!!!!!!!!!!!!temporary else block, remove immediately after fixing QRScanner!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    else:
                        data = "25MCA002,2531,ABHAJ KHAN"
                        self.logger.debug(f"cv2 not Detected!! using Hard Coded Data for completing workflow: {data}")
                        self._handle_scan(data, None)
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!temporary else block, remove immediately after fixing QRScanner!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                
                except Exception as e:
                    self.logger.error(f"cv2 detection error: {e}")

            if codes:
                self.logger.debug(f"Detected {len(codes)} codes")
                for code in codes:
                    payload = None
                    try:
                        payload = code.data.decode("utf-8")
                    except Exception as e:
                        self.logger.error(f"Error decoding payload: {e}")
                        continue
                    
                    rect = code.rect
                    scale_w = frame_disp.shape[1] / frame.shape[1]
                    scale_h = frame_disp.shape[0] / frame.shape[0]
                    rx = int(rect.left * scale_w)
                    ry = int(rect.top * scale_h)
                    rw = int(rect.width * scale_w)
                    rh = int(rect.height * scale_h)
                    
                    self._handle_scan(payload, (rx, ry, rw, rh))

            time.sleep(0.02)

        # cleanup camera on exit
        try:
            self.cap.release()
        except Exception:
            pass

    def _handle_scan(self, payload, rect):
        # debounce: ignore very recent same payload
        now = time.time()
        last = self.recent_scans.get(payload, 0)
        if now - last < 1.5:
            return
        self.recent_scans[payload] = now

        # spawn DB handling on a worker thread so UI stays smooth
        t = Thread(target=self._process_payload, args=(payload, rect), daemon=True)
        t.start()

    def _play_beep(self, success=True):
        """Try platform-friendly beep. Fallback to terminal bell."""
        try:
            if winsound and platform.system() == "Windows":
                winsound.MessageBeep(winsound.MB_OK if success else winsound.MB_ICONHAND)
                return
            if sa:
                # you can ship a tiny 'beep.wav' and load it instead for consistent sound
                # here we simply attempt a short tone using numpy+simpleaudio if available
                import numpy as np
                freq = 880 if success else 440
                duration_s = 0.12
                fs = 44100
                t = np.linspace(0, duration_s, int(fs*duration_s), False)
                tone = np.sin(freq * t * 2 * np.pi)
                audio = (tone * 32767).astype(np.int16)
                play_obj = sa.play_buffer(audio, 1, 2, fs)
                # no blocking
                return
            # fallback: system bell (may or may not produce sound)
            print('\a', end='', flush=True)
        except Exception:
            pass

    def _set_overlay(self, rect=None, msg="", color=(0,255,0), ttl=None):
        """Thread-safe setter for the overlay data. Use from worker threads."""
        def _apply():
            self.last_overlay = {
                "rect": rect,
                "msg": msg,
                "color": color,
                "ts": time.time(),
                "ttl": ttl or self.overlay_ttl
            }
        try:
            self.video_label.after(0, _apply)
        except Exception:
            # as a very last resort set directly
            self.last_overlay = {
                "rect": rect,
                "msg": msg,
                "color": color,
                "ts": time.time(),
                "ttl": ttl or self.overlay_ttl
            }

    def _process_payload(self, payload:str, rect):
        """
        Parse payload, write to DB, then update UI overlay + status. Runs in worker thread.
        """
        db = SessionLocal()
        try:
            student = None
            if payload:
                payload = payload.split(',')[0]
                student = db.query(StudentModel).filter(StudentModel.roll_no == payload).first()
            if student is None:
                student = db.query(StudentModel).filter(
                    (StudentModel.roll_no == payload) |
                    (StudentModel.admission_no == payload) |
                    (StudentModel.name == payload)
                ).first()
            if student is None:
                # unknown card
                self._set_overlay(rect=rect, msg=f"Unknown QR: {payload}", color=(0,0,255))
                self.logger.warning(f"Unknown QR code scanned: {payload}")
                self._play_beep(success=False)
                return

            # existing registry handling
            reg:RegistryModel = db.query(RegistryModel).filter(
                RegistryModel.session_id == self.session_row.id,
                RegistryModel.student_id == student.id
            ).order_by(RegistryModel.id.desc()).first()

            now_dt = datetime.now()
            if reg is None:
                # check-in
                new_reg = RegistryModel(student_id=student.id, session_id=self.session_row.id, check_in_time=now_dt, check_out_time=None)
                db.add(new_reg)
                db.commit()
                db.refresh(new_reg)
                db.refresh(new_reg)
                msg = f"Checked IN: {student.name}"
                self.logger.info(f"Student Checked IN: {student.name} (ID: {student.id})")
                color = (0,255,0)
            else:
                if now_dt > datetime.combine(datetime.today(), reg.check_in_time) + timedelta(minutes=15):
                # check-out
                    reg.check_out_time = now_dt
                    db.add(reg)
                    db.commit()
                    db.add(reg)
                    db.commit()
                    msg = f"Checked OUT: {student.name}"
                    self.logger.info(f"Student Checked OUT: {student.name} (ID: {student.id})")
                    color = (255,200,0)  # amber-ish for checkout
                else:
                    self.logger.warning(f"Student already Checked IN Just Now: {student.name} (ID: {student.id})")
                    #TODO: handle this case!!!
                    msg = f"Already Checked IN: {student.name}"
                    color = (0,0,255)
            # success: update overlay and status label (UI thread)
            self._set_overlay(rect=rect, msg=msg, color=color)
            self.video_label.after(0, lambda: self.status.config(text=msg, bootstyle="success"))

            # play beep
            self._play_beep(success=True)

        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            self._set_overlay(rect=rect, msg="DB error", color=(0,0,255))
            self.video_label.after(0, lambda: self.status.config(text=f"DB error: {e}", bootstyle="danger"))
            self.logger.error(f"Database error during processing payload: {e}")
            self._play_beep(success=False)
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
        self.logger.info("Scanner stopped.")
