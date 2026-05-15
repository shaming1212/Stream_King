import os
import logging
import keyboard
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from gui.widgets.top_bar import TopBar
from gui.widgets.bottom_nav import BottomNav
from gui.widgets.audio_wave import AudioWaveWidget
from gui.signal_bridge import VoiceEngineBridge, CameraBridge, ModelLoaderThread
from core.config import HOTKEY_VOICE, HOTKEY_CAMERA, HOTKEY_SCREENSHOT
from core.screenshot_tool import capture_fullscreen, crop_to_jpeg_base64
from server.ws_server import ws_manager

logger = logging.getLogger("main_window")


class MainWindow(QMainWindow):
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
        self._connect_signals()

        self._history = []

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
        self.hint_label.setText("首次运行需下载模型，请耐心等待")
        self._loading_counter = 0
        self._loading_timer.start(5000)

    def _on_loading_tick(self):
        self._loading_counter += 1
        dots = "." * ((self._loading_counter % 3) + 1)
        self.hint_label.setText(f"模型首次下载约需 2-10 分钟{dots}")

    def _on_model_ready(self):
        self._loading_timer.stop()
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.help_label.setText("How can I help?")
        self.hint_label.setText(f"按住  {hk}  说话，松开出字")
        self.bridge.engine.start_listening()
        try:
            keyboard.add_hotkey(HOTKEY_CAMERA, self._on_camera)
        except Exception as e:
            logger.warning("camera hotkey: %s", e)
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
        import datetime
        self._history.append({"type": "voice", "text": text,
                              "time": datetime.datetime.now().strftime("%H:%M:%S")})
        ws_manager.broadcast_text(text)

    def _on_error(self, msg):
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        self.help_label.setText(f"❌ {msg}")
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.hint_label.setText(f"按住  {hk}  重试")

    # ── camera ──
    def _on_camera(self):
        logger.info("CAMERA HOTKEY TRIGGERED")
        self.help_label.setText("Alt+2 triggered!")
        self._set_dot("#FFB800")
        import threading
        threading.Thread(target=self.camera_bridge.capture, daemon=True).start()

    def _on_capture_success(self, b64):
        self.status_label.setText("READY")
        self._set_dot("#00D4A0")
        self.help_label.setText("\U0001F4F7 照片已推送")
        import datetime
        self._history.append({"type": "camera", "data": b64,
                              "time": datetime.datetime.now().strftime("%H:%M:%S")})
        ws_manager.broadcast_image(b64)

    def _on_capture_error(self, msg):
        self.status_label.setText("READY")
        self._set_dot("#FF4444")
        self.help_label.setText(f"\U0001F4F7 拍照失败: {msg}")

    # ── screenshot ──
    def _on_screenshot(self):
        logger.info("SCREENSHOT HOTKEY TRIGGERED")
        self.help_label.setText("Alt+3 triggered!")
        self._set_dot("#FFB800")
        import threading
        threading.Thread(target=self._do_screenshot, daemon=True).start()

    def _do_screenshot(self):
        try:
            img = capture_fullscreen()
            h, w = img.shape[:2]
            b64 = crop_to_jpeg_base64(img, 0, 0, w, h)
            import datetime
            self._history.append({"type": "screenshot", "data": b64,
                                  "time": datetime.datetime.now().strftime("%H:%M:%S")})
            ws_manager.broadcast_image(b64)
            self.status_label.setText("READY")
            self._set_dot("#00D4A0")
            self.help_label.setText("\U0001F4F7 全屏截图已推送")
        except Exception as e:
            logger.error("screenshot: %s", e)
            self._set_dot("#FF4444")
            self.help_label.setText(f"\U0001F4F7 截图失败: {e}")

    # ── buttons ──
    def _on_mic_clicked(self):
        hk = HOTKEY_VOICE.replace("+", " + ").upper()
        self.help_label.setText("\U0001F399")
        self.hint_label.setText(f"按住  {hk}  开始说话")

    def _on_history_clicked(self):
        from gui.widgets.history_dialog import HistoryDialog
        dlg = HistoryDialog(self._history, self)
        dlg.cleared.connect(self._history.clear)
        dlg.exec()

    def _on_settings_clicked(self):
        QMessageBox.information(self, "设置", "更多设置选项将在后续版本中提供。\n当前可在 core/config.py 中修改配置。")

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
        ws_manager.stop()
        import time
        time.sleep(0.2)
        super().closeEvent(event)
