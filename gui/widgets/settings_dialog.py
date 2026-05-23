import logging
from PyQt6.QtWidgets import (QDialog, QTabWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QPushButton, QComboBox, QWidget, QLineEdit,
                                 QFileDialog, QProgressBar, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from server.ws_server import ws_manager
from server.file_server import file_server
from core.camera_engine import CameraEngine
from core.config import MODEL_NAME

logger = logging.getLogger("settings_dialog")


class SettingsDialog(QDialog):
    def __init__(self, camera_engine: CameraEngine, voice_engine, parent=None):
        super().__init__(parent)
        self.camera_engine = camera_engine
        self.voice_engine = voice_engine
        self.setWindowTitle("AURA 设置")
        self.setMinimumSize(420, 380)
        self.setStyleSheet("""
            QDialog { background-color: #14141A; color: #E0E0E0; }
            QTabWidget::pane { border: 1px solid #2A2A35; background: #1A1A22; }
            QTabBar::tab { background: #1A1A22; color: #888; padding: 8px 20px;
                           border: 1px solid #2A2A35; border-bottom: none; }
            QTabBar::tab:selected { background: #252530; color: #00D4A0; }
            QLabel { color: #C0C0C0; }
            QPushButton { background: #00D4A0; color: #0C0C10; border: none;
                          border-radius: 4px; padding: 6px 16px; font-weight: bold; }
            QPushButton:hover { background: #00FFB0; }
            QPushButton:disabled { background: #333; color: #666; }
            QComboBox { background: #1A1A22; color: #E0E0E0; border: 1px solid #2A2A35;
                        border-radius: 4px; padding: 4px 8px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1A1A22; color: #E0E0E0;
                                          selection-background-color: #00D4A0; }
            QLineEdit { background: #1A1A22; color: #E0E0E0; border: 1px solid #2A2A35;
                        border-radius: 4px; padding: 4px 8px; }
            .StatusDot { border-radius: 5px; min-width: 10px; max-width: 10px;
                         min-height: 10px; max-height: 10px; }
            .SectionTitle { color: #00D4A0; font-size: 14px; font-weight: bold; }
            .Value { color: #E0E0E0; font-family: monospace; }
        """)

        self.tabs = QTabWidget()
        self._build_connection_tab()
        self._build_model_tab()
        self._build_camera_tab()
        self._build_file_tab()

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_connection)
        self._refresh_timer.start(2000)

    # ── Connection Tab ──
    def _build_connection_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)

        lay.addWidget(self._section("连接状态"))
        self.status_dot = QLabel()
        self.status_dot.setObjectName("statusDot")
        self.status_label = QLabel("运行中")
        row = QHBoxLayout()
        row.addWidget(self.status_dot)
        row.addWidget(self.status_label)
        row.addStretch()
        lay.addLayout(row)

        lay.addWidget(self._section("服务地址"))
        lay.addWidget(QLabel("wss://127.0.0.1:8765"))

        lay.addWidget(self._section("已连接客户端"))
        self.client_count_label = QLabel("0")
        self.client_count_label.setStyleSheet("font-size: 24px; color: #00D4A0; font-weight: bold;")
        lay.addWidget(self.client_count_label)

        lay.addStretch()
        self.tabs.addTab(w, "连接")

    # ── Model Tab ──
    def _build_model_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)

        lay.addWidget(self._section("当前模型"))
        self.current_model_label = QLabel(MODEL_NAME)
        self.current_model_label.setStyleSheet("color: #E0E0E0; font-family: monospace;")
        self.current_model_label.setWordWrap(True)
        lay.addWidget(self.current_model_label)

        lay.addWidget(self._section("切换模型"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "iic/SenseVoiceSmall",
            "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        ])
        self.model_combo.setCurrentText(MODEL_NAME)
        lay.addWidget(self.model_combo)

        self.model_custom = QLineEdit()
        self.model_custom.setPlaceholderText("或输入其他 ModelScope 模型名...")
        lay.addWidget(self.model_custom)

        btn_row = QHBoxLayout()
        self.model_switch_btn = QPushButton("切换并重新加载")
        self.model_switch_btn.clicked.connect(self._on_switch_model)
        btn_row.addWidget(self.model_switch_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self.model_status = QLabel("")
        self.model_status.setStyleSheet("color: #FFB800;")
        lay.addWidget(self.model_status)

        lay.addStretch()
        self.tabs.addTab(w, "模型")

    # ── Camera Tab ──
    def _build_camera_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)

        lay.addWidget(self._section("可用摄像头"))
        self.camera_combo = QComboBox()
        self._refresh_cameras()
        lay.addWidget(self.camera_combo)

        btn_row = QHBoxLayout()
        self.camera_switch_btn = QPushButton("切换摄像头")
        self.camera_switch_btn.clicked.connect(self._on_switch_camera)
        btn_row.addWidget(self.camera_switch_btn)

        self.camera_test_btn = QPushButton("测试拍照")
        self.camera_test_btn.clicked.connect(self._on_test_camera)
        btn_row.addWidget(self.camera_test_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self.camera_status = QLabel("")
        lay.addWidget(self.camera_status)

        lay.addStretch()
        self.tabs.addTab(w, "摄像头")

    # ── File Transfer Tab ──
    def _build_file_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)

        lay.addWidget(self._section("已选文件"))
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMinimumHeight(120)
        self.file_list_widget.setStyleSheet("""
            QListWidget { background: #0C0C10; border: 1px solid #22222E;
                          border-radius: 6px; color: #C8C8D4; font-size: 12px; padding: 4px; }
            QListWidget::item { padding: 4px 2px; }
            QListWidget::item:hover { background: #1A1A24; }
        """)
        lay.addWidget(self.file_list_widget)

        self.file_summary_label = QLabel("未选择文件")
        self.file_summary_label.setStyleSheet("color: #888; font-family: monospace;")
        lay.addWidget(self.file_summary_label)

        btn_row = QHBoxLayout()
        self.file_select_btn = QPushButton("选择文件...")
        self.file_select_btn.clicked.connect(self._on_select_files)
        btn_row.addWidget(self.file_select_btn)

        self.file_clear_btn = QPushButton("清空")
        self.file_clear_btn.setEnabled(False)
        self.file_clear_btn.clicked.connect(self._on_clear_files)
        btn_row.addWidget(self.file_clear_btn)

        self.file_send_btn = QPushButton("发送到手机")
        self.file_send_btn.setEnabled(False)
        self.file_send_btn.clicked.connect(self._on_send_files)
        btn_row.addWidget(self.file_send_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self.file_status = QLabel("")
        lay.addWidget(self.file_status)

        self._selected_files = []
        self._sending = False

        lay.addStretch()
        self.tabs.addTab(w, "文件传输")

    def _on_select_files(self):
        import os
        paths, _ = QFileDialog.getOpenFileNames(self, "选择要发送的文件")
        if not paths:
            return
        for p in paths:
            if p not in self._selected_files:
                self._selected_files.append(p)
                name = os.path.basename(p)
                size = os.path.getsize(p)
                size_str = f"{size / 1024 / 1024:.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
                self.file_list_widget.addItem(f"{name}  ({size_str})")
        self._update_file_summary()

    def _on_clear_files(self):
        self._selected_files.clear()
        self.file_list_widget.clear()
        self._update_file_summary()

    def _update_file_summary(self):
        import os
        n = len(self._selected_files)
        if n == 0:
            self.file_summary_label.setText("未选择文件")
            self.file_send_btn.setEnabled(False)
            self.file_clear_btn.setEnabled(False)
        else:
            total = sum(os.path.getsize(p) for p in self._selected_files)
            total_str = f"{total / 1024 / 1024:.1f} MB" if total > 1024 * 1024 else f"{total / 1024:.1f} KB"
            self.file_summary_label.setText(f"{n} 个文件，共 {total_str}")
            self.file_send_btn.setEnabled(True)
            self.file_clear_btn.setEnabled(True)
        self.file_status.setText("")

    def _on_send_files(self):
        if not self._selected_files or self._sending:
            return
        if not ws_manager.clients:
            self.file_status.setText("没有已连接的手机客户端")
            self.file_status.setStyleSheet("color: #FF4444;")
            return

        self._sending = True
        self.file_send_btn.setEnabled(False)
        self.file_select_btn.setEnabled(False)
        self.file_clear_btn.setEnabled(False)
        self.file_status.setText("发送中...")
        self.file_status.setStyleSheet("color: #FFB800;")

        import threading
        threading.Thread(target=self._do_send_files, daemon=True).start()

    def _do_send_files(self):
        import time
        sent = 0
        failed = 0
        total = len(self._selected_files)

        for i, filepath in enumerate(self._selected_files):
            import os
            name = os.path.basename(filepath)
            self._update_file_status(f"({i + 1}/{total}) 发送: {name}")
            try:
                filename = file_server.start_with_file(filepath)
                ws_manager.send_file_to_mobile(filename)
                delivered = file_server.delivered.wait(timeout=60)
                file_server.stop()

                if delivered:
                    sent += 1
                else:
                    failed += 1
                    logger.warning("file transfer timeout: %s", filename)
            except Exception as e:
                failed += 1
                logger.error("file transfer error: %s", e)
                try:
                    file_server.stop()
                except Exception:
                    pass

            if i < total - 1:
                time.sleep(0.5)

        self._selected_files.clear()
        self._update_file_status_done(sent, failed)

    def _update_file_status(self, text):
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self.file_status, "setText",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, text))

    def _update_file_status_done(self, sent, failed):
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        if failed == 0:
            msg = f"全部 {sent} 个文件已送达"
            color = "#00D4A0"
        else:
            msg = f"送达 {sent} 个，失败 {failed} 个"
            color = "#FFB800"
        QMetaObject.invokeMethod(self.file_status, "setText",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, msg))
        QMetaObject.invokeMethod(self.file_status, "setStyleSheet",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, f"color: {color};"))
        # Re-enable buttons on UI thread
        QTimer.singleShot(0, self._reset_file_ui)

    def _reset_file_ui(self):
        self.file_list_widget.clear()
        self._sending = False
        self.file_select_btn.setEnabled(True)
        self._update_file_summary()

    # ── helpers ──
    def _section(self, title):
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #00D4A0; font-size: 13px; font-weight: bold;")
        return lbl

    def _refresh_connection(self):
        count = len(ws_manager.clients)
        self.client_count_label.setText(str(count))
        if ws_manager.loop and not ws_manager.loop.is_closed():
            self.status_label.setText("运行中")
            self.status_dot.setStyleSheet("background-color: #00D4A0; border-radius: 5px;")
        else:
            self.status_label.setText("已停止")
            self.status_dot.setStyleSheet("background-color: #FF4444; border-radius: 5px;")

    def _refresh_cameras(self):
        self.camera_combo.clear()
        cams = CameraEngine.list_cameras()
        for i in cams:
            self.camera_combo.addItem(f"摄像头 {i} (device_index={i})", i)
        if not cams:
            self.camera_combo.addItem("未检测到摄像头", -1)

    def _on_switch_camera(self):
        idx = self.camera_combo.currentData()
        if idx is None or idx < 0:
            self.camera_status.setText("❌ 无可用摄像头")
            self.camera_status.setStyleSheet("color: #FF4444;")
            return
        self.camera_engine.switch_camera(idx)
        self.camera_status.setText(f"✅ 已切换到摄像头 {idx}")
        self.camera_status.setStyleSheet("color: #00D4A0;")

    def _on_test_camera(self):
        try:
            b64 = self.camera_engine.capture_frame_base64()
            self.camera_status.setText(f"✅ 拍照成功 ({len(b64)} bytes)")
            self.camera_status.setStyleSheet("color: #00D4A0;")
        except Exception as e:
            self.camera_status.setText(f"❌ 拍照失败: {e}")
            self.camera_status.setStyleSheet("color: #FF4444;")

    def _on_switch_model(self):
        new_model = self.model_custom.text().strip() or self.model_combo.currentText()
        if new_model == MODEL_NAME:
            self.model_status.setText("已经是当前模型")
            self.model_status.setStyleSheet("color: #FFB800;")
            return

        self.model_switch_btn.setEnabled(False)
        self.model_status.setText(f"⏳ 正在下载模型 {new_model} ...")
        self.model_status.setStyleSheet("color: #FFB800;")
        import threading
        threading.Thread(target=self._do_switch_model, args=(new_model,), daemon=True).start()

    def _do_switch_model(self, new_model):
        try:
            self.voice_engine.stop_listening()
            from modelscope.hub.snapshot_download import snapshot_download
            from funasr import AutoModel
            model_path = snapshot_download(new_model)
            vad_path = snapshot_download("iic/speech_fsmn_vad_zh-cn-16k-common-pytorch")
            punc_path = snapshot_download("iic/punc_ct-transformer_cn-en-common-vocab471067-large")
            self.voice_engine.model = AutoModel(
                model=model_path, vad_model=vad_path, punc_model=punc_path, disable_update=True)
            import core.config as cfg
            cfg.MODEL_NAME = new_model
            self.model_status.setText(f"✅ 模型已切换: {new_model}")
            self.model_status.setStyleSheet("color: #00D4A0;")
            self.current_model_label.setText(new_model)
            self.voice_engine.start_listening()
        except Exception as e:
            self.model_status.setText(f"❌ 切换失败: {e}")
            self.model_status.setStyleSheet("color: #FF4444;")
            self.voice_engine.start_listening()
        finally:
            self.model_switch_btn.setEnabled(True)
