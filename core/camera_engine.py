import base64
import threading


class CameraEngine:
    def __init__(self, device_index=0):
        self.device_index = device_index
        self.cap = None
        self._lock = threading.Lock()

    def capture_frame_base64(self) -> str:
        import cv2
        with self._lock:
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.device_index)
            ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("无法读取摄像头画面")
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def release(self):
        with self._lock:
            if self.cap:
                self.cap.release()
                self.cap = None
