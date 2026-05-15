from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal


class HistoryDialog(QDialog):
    cleared = pyqtSignal()

    def __init__(self, history: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录")
        self.setMinimumSize(360, 400)

        self.setStyleSheet("""
            QDialog { background-color: #14141A; }
            QLabel { color: #E8E8EC; font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; background: transparent; }
            QListWidget { background-color: #0C0C10; border: 1px solid #22222E; border-radius: 8px; color: #C8C8D4; font-size: 13px; padding: 8px; outline: none; }
            QListWidget::item { border-bottom: 1px solid #1E1E28; padding: 10px 4px; }
            QListWidget::item:last { border-bottom: none; }
            QPushButton { background-color: #18181E; border: 1px solid #25252D; border-radius: 8px; color: #AAAABC; font-size: 12px; padding: 8px 20px; }
            QPushButton:hover { background-color: #20202A; border: 1px solid #35354A; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("语音 / 图片历史")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F0F0F4;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        if history:
            for h in reversed(history):
                self._add_item(h)
        else:
            self.list_widget.addItem("暂无历史记录")
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("QPushButton { background-color: #0A2520; border: 1px solid #0D3830; color: #00D4A0; } QPushButton:hover { background-color: #0D3028; border: 1px solid #10503E; }")
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _add_item(self, h: dict):
        t = h.get("type", "voice")
        ts = h.get("time", "")
        if t == "voice":
            text = h.get("text", "")
            display = f"\U0001F399 {ts}  {text}"
        else:
            display = f"\U0001F4F7 {ts}  图片"
        self.list_widget.addItem(display)

    def _clear(self):
        self.list_widget.clear()
        self.list_widget.addItem("暂无历史记录")
        self.cleared.emit()
