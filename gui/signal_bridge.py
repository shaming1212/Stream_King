from PyQt6.QtCore import QObject, pyqtSignal, QThread
from core.voice_engine import VoiceEngine
from core.camera_engine import CameraEngine
from core.screenshot_tool import capture_fullscreen, crop_to_jpeg_base64


class VoiceEngineBridge(QObject):
    sig_model_loading = pyqtSignal()
    sig_model_ready = pyqtSignal()
    sig_model_error = pyqtSignal(str)
    sig_recording_start = pyqtSignal()
    sig_recording_stop = pyqtSignal()
    sig_processing = pyqtSignal()
    sig_result = pyqtSignal(str)
    sig_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.engine = VoiceEngine()
        self.engine.on_model_loading = self.sig_model_loading.emit
        self.engine.on_model_ready = self.sig_model_ready.emit
        self.engine.on_model_error = self.sig_model_error.emit
        self.engine.on_recording_start = self.sig_recording_start.emit
        self.engine.on_recording_stop = self.sig_recording_stop.emit
        self.engine.on_processing = self.sig_processing.emit
        self.engine.on_result = self.sig_result.emit
        self.engine.on_error = self.sig_error.emit


class CameraBridge(QObject):
    sig_success = pyqtSignal(str)
    sig_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.camera = CameraEngine()

    def capture(self):
        try:
            b64 = self.camera.capture_frame_base64()
            self.sig_success.emit(b64)
        except Exception as e:
            self.sig_error.emit(str(e))

    def list_cameras(self):
        return CameraEngine.list_cameras()

    def release(self):
        self.camera.release()


class ModelLoaderThread(QThread):
    def __init__(self, engine: VoiceEngine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            self.engine.init_model()
        except Exception as e:
            self.engine._emit(self.engine.on_model_error, str(e))
