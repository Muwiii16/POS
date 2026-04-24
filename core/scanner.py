import threading
import time
import cv2
from pyzbar.pyzbar import decode
from cv2_enumerate_cameras import enumerate_cameras


def get_available_cameras():
    cameras = []

    try:
        for cam in enumerate_cameras(cv2.CAP_MSMF):
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
        self._cooldown = 2.0

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

        last_scan_time = 0
        fail_count = 0

        while self._running:
            ret, frame = cap.read()
            if not ret:
                fail_count += 1
                if fail_count >= 30:
                    cap.release()
                    time.sleep(2.0)
                    cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)
                    fail_count = 0
                else:
                    time.sleep(0.1)
                continue

            fail_count = 0

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            barcodes = decode(gray)

            for b in barcodes:
                barcode_val = b.data.decode('utf-8')
                now = time.time()

                if barcode_val == self._last_scanned and (now - last_scan_time) < self._cooldown:
                    continue

                self._last_scanned = barcode_val
                last_scan_time = now
                self.on_scan(barcode_val)

            time.sleep(0.05)
        cap.release()
