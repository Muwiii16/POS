import threading
import time
import cv2
import winsound
from pyzbar.pyzbar import decode, ZBarSymbol
from cv2_enumerate_cameras import enumerate_cameras


def get_available_cameras():
    cameras = []

    try:
        for cam in enumerate_cameras(cv2.CAP_DSHOW):
            cameras.append((cam.index, cam.name))
    except Exception:
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
            if cap.isOpened():
                cameras.append((i, f'Camera{i}'))
                cap.release()
    return cameras


class BarcodeScanner:
    def __init__(self, on_scan_callback, camera_index=0):
        self.on_scan = on_scan_callback
        self.camera_index = camera_index
        self._thread = None
        self._running = False
        self._last_scanned = None
        self._barcode_present = False
        self._empty_frames = 0
        self._reset_after = 20
        self._lock = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def switch_camera(self, new_index):
        self.stop()
        time.sleep(0.3)
        self.camera_index = new_index
        self._running = False
        self.start()

    def _scan_loop(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)
        if not cap.isOpened():
            print('Scanner: could not open webcam.')
            return

        fail_count = 0
        startup_frames = 0
        startup_skip = 10

        while self._running:
            ret, frame = cap.read()
            if not ret:
                fail_count += 1
                if fail_count >= 30:
                    cap.release()
                    time.sleep(2.0)
                    cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                    fail_count = 0
                else:
                    time.sleep(0.1)
                continue

            fail_count = 0

            if startup_frames < startup_skip:
                startup_frames += 1
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            barcodes = decode(gray, symbols=[ZBarSymbol.CODE128])

            if barcodes:
                barcode_val = barcodes[0].data.decode('utf-8')
                self._empty_frames = 0

                if not self._barcode_present or barcode_val != self._last_scanned:
                    with self._lock:
                        self._last_scanned = barcode_val
                        self._barcode_present = True
                        winsound.Beep(1000, 80)
                        self.on_scan(barcode_val)
            else:
                self._barcode_present = False

            time.sleep(0.02)

        cap.release()
