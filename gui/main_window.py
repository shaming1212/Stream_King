import os
import time
import logging
import keyboard
import numpy as np
import cv2
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QMessageBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from gui.widgets.top_bar import TopBar
from gui.widgets.bottom_nav import BottomNav
from gui.widgets.audio_wave import AudioWaveWidget
from gui.signal_bridge import VoiceEngineBridge, CameraBridge, ModelLoaderThread
from core.config import HOTKEY_VOICE, HOTKEY_CAMERA, HOTKEY_SCREENSHOT
from core.screenshot_tool import capture_fullscreen, crop_to_jpeg_base64
from core.clipboard_util import set_clipboard_image
from core.history_store import HistoryStore
from server.ws_server import ws_manager

logger = logging.getLogger("main_window")


class MainWindow(QMainWindow):
    sig_screenshot_result = pyqtSignal(bool, str)  # success, data|error_msg
    sig_clipboard_image = pyqtSignal(object)  # numpy BGR image for clipboard

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AURA Voice Assistant")
        self.setMinimumSize(400, 720)
        self.setStyleSheet("background-color: #0C0C10;")

        central = QWidget()
        central.setObjectName("MainPanel")
        self.setCentralWidget(central)

        self._build_ui(central)
        self._load_stylesheet()

        self.bridge = VoiceEngineBridge()
        self.camera_bridge = CameraBridge()
        self._history = HistoryStore()

        # Wire mobile events through desktop processing pipeline
        ws_manager.on_mobile_image = self._on_mobile_image
        ws_manager.on_mobile_audio = self._on_mobile_audio
        ws_manager.on_file_received = self._on_file_received

        self._connect_signals()

        self._camera_cd = 0.0
        self._screenshot_cd = 0.0

        self._loading_counter = 0
        self._loading_timer = QTimer()
        self._loading_timer.timeout.connect(self._on_loading_tick)

        self.loader_thread = ModelLoaderThread(self.bridge.engine)
        self.loader_thread.start()

    def _build_ui(self, parent):
        root = QVBoxLayout(parent)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.top_bar = TopBar()
        root.addWidget(self.top_bar)

        sep = QFrame()
        sep.setObjectName("separatorLine")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        root.addStretch(2)

        wave_box = QHBoxLayout()
        wave_box.setContentsMargins(28, 0, 28, 0)
        self.audio_wave = AudioWaveWidget()
        wave_box.addWidget(self.audio_wave)
        root.addLayout(wave_box)

        root.addSpacing(28)

        badge_row = QHBoxLayout()
        badge_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge = QWidget()
        badge.setObjectName("statusBadge")
        badge.setFixedSize(180, 30)
        badge_inner = QHBoxLayout(badge)
        badge_inner.setContentsMargins(14, 0, 14, 0)
        badge_inner.setSpacing(8)

        self.status_dot = QWidget()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(8, 8)
        self.status_label = QLabel("正在加载模型...")
        self.status_label.setObjectName("statusLabel")
        badge_inner.addWidget(self.status_dot)
        badge_inner.addWidget(self.status_label)
        badge_row.addWidget(badge)
        root.addLayout(badge_row)

        root.addSpacing(14)

        self.help_label = QLabel("正在初始化...")
        self.help_label.setObjectName("helpLabel")
        self.help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.help_label.setWordWrap(True)
        self.help_label.setContentsMargins(24, 0, 24, 0)
        root.addWidget(self.help_label)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.hint_label)

        root.addStretch(3)

        nav_box = QHBoxLayout()
        nav_box.setContentsMargins(20, 0, 20, 16)
        self.bottom_nav = BottomNav()
        nav_box.addWidget(self.bottom_nav)
        root.addLayout(nav_box)

    def _connect_signals(self):
        self.bridge.sig_model_loading.connect(self._on_model_loading)
        self.bridge.sig_model_ready.connect(self._on_model_ready)
        self.bridge.sig_model_error.connect(self._on_model_error)
        self.bridge.sig_recording_start.connect(self._on_recording_start)
        self.bridge.sig_recording_stop.connect(self._on_recording_stop)
        self.bridge.sig_processing.connect(self._on_processing)
        self.bridge.sig_result.connect(self._on_result)
        self.bridge.sig_error.connect(self._on_error)

        self.camera_bridge.sig_success.connect(self._on_capture_success)
        self.camera_bridge.sig_error.connect(self._on_capture_error)
        self.sig_screenshot_result.connect(self._on_screenshot_result)
        self.sig_clipboard_image.connect(self._set_clipboard)

        self.bottom_nav.btn_mic.clicked.connect(self._on_mic_clicked)
        self.bottom_nav.btn_history.clicked.connect(self._on_history_clicked)
        self.bottom_nav.btn_settings.clicked.connect(self._on_settings_clicked)
        self.top_bar.menu_btn.clicked.connect(self._on_menu_clicked)

    def _set_dot(self, color):
        self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

    def _on_model_loading(self):
        self.status_label.setText("LOADING...")
        self._set_dot("#FFB800")
        self.help_label.setText("正在加载 AI 模型...")
        from core.config import MODEL_CACHE_DIR, MODEL_NAME
        self.hint_label.setText(f"模型: {MODEL_NAME}；缓存目录: {MODEL_CACHE_DIR}")
        self._loading_counter = 0
        self._loading_timer.start(5000)

    def _on_loading_tick(self):
        self._loading_counter += 1
        dots = "." * ((self._loading_counter % 3) + 1)
        self.hint_label.setText(f"首次运行会下载模型；后续启动使用本地缓存{dots}")

    def _on_model_ready(self):
        self._loading_timer.stop()
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.help_label.setText("How can I help?")
        self.hint_label.setText(f"按住  {hk}  说话，松开出字")
        self.bridge.engine.start_listening()
        cameras = self.camera_bridge.list_cameras()
        if cameras:
            try:
                keyboard.add_hotkey(HOTKEY_CAMERA, self._on_camera)
            except Exception as e:
                logger.warning("camera hotkey: %s", e)
        else:
            logger.warning("no camera detected, skipping camera hotkey")
            self.hint_label.setText(f"按住  {hk}  说话，松开出字 (无摄像头)")
        try:
            keyboard.add_hotkey(HOTKEY_SCREENSHOT, self._on_screenshot)
        except Exception as e:
            logger.warning("screenshot hotkey: %s", e)

    def _on_model_error(self, msg):
        self._loading_timer.stop()
        self.status_label.setText("ERROR")
        self._set_dot("#FF4444")
        self.help_label.setText("模型加载失败")
        self.hint_label.setText(msg[:60])

    def _on_recording_start(self):
        self.status_label.setText("LISTENING...")
        self._set_dot("#00FF88")
        self.help_label.setText("\U0001F399 正在聆听...")
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.hint_label.setText(f"松开 {hk} 结束录音")
        self.audio_wave.set_active(True)

    def _on_recording_stop(self):
        self.audio_wave.set_active(False)

    def _on_processing(self):
        self.status_label.setText("PROCESSING...")
        self._set_dot("#FFB800")
        self.help_label.setText("识别中...")
        self.hint_label.setText("")

    def _on_result(self, text):
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        display = text if len(text) <= 30 else text[:30] + "..."
        self.help_label.setText(f"✅ {display}")
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.hint_label.setText(f"按住  {hk}  继续说话")
        self._history.add_voice(text)
        ws_manager.broadcast_text(text, send=True)

    def _on_error(self, msg):
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        self.help_label.setText(f"❌ {msg}")
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.hint_label.setText(f"按住  {hk}  重试")

    # ── camera ──
    def _on_camera(self):
        now = time.monotonic()
        if now - self._camera_cd < 1.0:
            return
        self._camera_cd = now
        logger.info("CAMERA HOTKEY TRIGGERED")
        self.help_label.setText("Alt+2 triggered!")
        self._set_dot("#FFB800")
        import threading
        threading.Thread(target=self.camera_bridge.capture, daemon=True).start()

    def _on_capture_success(self, b64):
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        self.help_label.setText("\U0001F4F7 照片已复制到剪贴板")
        self.hint_label.setText("切到 AI 页面按 Ctrl+V 粘贴")
        self._history.add_image(b64, "camera")
        ws_manager.broadcast_image(b64)
        self._b64_to_clipboard(b64)

    def _on_capture_error(self, msg):
        logger.error("camera capture failed: %s", msg)
        self.status_label.setText("READY")
        self._set_dot("#FF4444")
        self.help_label.setText(f"\U0001F4F7 拍照失败: {msg}")

    def _on_mobile_image(self, b64: str):
        self._history.add_image(b64, "mobile")
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        self.help_label.setText("📱 已收到手机图片")
        self.hint_label.setText("已确认手机上传，正在转发插件并写入剪贴板")
        self._b64_to_clipboard(b64)
        logger.info("mobile image received → history + clipboard signal (broadcast handled by server)")

    def _set_clipboard(self, img):
        if set_clipboard_image(img):
            logger.info("image copied to clipboard")

    def _b64_to_clipboard(self, b64: str):
        import base64
        try:
            raw = b64.split(",")[-1]
            jpg_bytes = base64.b64decode(raw)
            img = cv2.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                # WebSocket 回调可能不在 Qt 主线程，使用 signal 切回主线程写剪贴板。
                self.sig_clipboard_image.emit(img)
        except Exception as e:
            logger.warning("b64 to clipboard failed: %s", e)

    def _on_mobile_audio(self, b64: str):
        self.bridge.engine.process_mobile_audio(b64)
        logger.info("mobile audio → ASR pipeline")

    def _on_file_received(self, filename: str):
        from server.file_server import file_server
        file_server.mark_delivered()
        logger.info("file delivered: %s", filename)

    # ── screenshot ──
    def _on_screenshot(self):
        now = time.monotonic()
        if now - self._screenshot_cd < 1.0:
            return
        self._screenshot_cd = now
        logger.info("SCREENSHOT HOTKEY TRIGGERED")
        self.help_label.setText("Alt+3 triggered!")
        self._set_dot("#FFB800")
        import threading
        threading.Thread(target=self._do_screenshot, daemon=True).start()

    def _do_screenshot(self):
        try:
            img = capture_fullscreen()
            self.sig_clipboard_image.emit(img)
            h, w = img.shape[:2]
            b64 = crop_to_jpeg_base64(img, 0, 0, w, h)
            self._history.add_image(b64, "screenshot")
            ws_manager.broadcast_image(b64)
            self.sig_screenshot_result.emit(True, b64)
        except Exception as e:
            logger.error("screenshot: %s", e)
            self.sig_screenshot_result.emit(False, str(e))

    def _on_screenshot_result(self, success: bool, data: str):
        if success:
            self.status_label.setText("READY")
            self._set_dot("#00D4A0")
            self.help_label.setText("\U0001F4F7 截图已复制到剪贴板")
            self.hint_label.setText("切到 AI 页面按 Ctrl+V 粘贴")
        else:
            self._set_dot("#FF4444")
            self.help_label.setText(f"\U0001F4F7 截图失败: {data}")

    # ── buttons ──
    def _on_mic_clicked(self):
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.help_label.setText("\U0001F399")
        self.hint_label.setText(f"按住  {hk}  开始说话")

    def _on_history_clicked(self):
        from gui.widgets.history_dialog import HistoryDialog
        dlg = HistoryDialog(self._history.records, self)
        dlg.cleared.connect(self._history.clear)
        dlg.exec()

    def _on_settings_clicked(self):
        from gui.widgets.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.camera_bridge.camera, self.bridge.engine, self)
        dlg.exec()

    def _on_menu_clicked(self):
        QMessageBox.about(self, "关于 AURA",
            "AURA Voice Assistant\n\n"
            "本地 AI 语音助手，基于 FunASR 语音识别引擎。\n"
            "搭配 Chrome 浏览器插件使用，支持语音输入到 DeepSeek。\n\n"
            f"快捷键:\n  {HOTKEY_VOICE}  按住说话\n  {HOTKEY_CAMERA}  拍照\n  {HOTKEY_SCREENSHOT}  截图")

    def _load_stylesheet(self):
        qss = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(qss):
            with open(qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def closeEvent(self, event):
        self._loading_timer.stop()
        self.bridge.engine.stop_listening()
        self.camera_bridge.release()
        from server.file_server import file_server
        file_server.cleanup()
        ws_manager.stop()
        import time
        time.sleep(0.2)
        super().closeEvent(event)
