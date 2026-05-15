from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt


class BottomNav(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("bottomNav")
        self.setFixedHeight(72)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(0)

        self.btn_mic = QPushButton("\U0001F399")
        self.btn_mic.setObjectName("micButton")
        self.btn_mic.setFixedSize(48, 48)
        self.btn_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mic.setToolTip("语音输入")

        self.btn_history = QPushButton("⏱")
        self.btn_history.setObjectName("navButton")
        self.btn_history.setFixedSize(44, 44)
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_history.setToolTip("历史记录")

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setObjectName("navButton")
        self.btn_settings.setFixedSize(44, 44)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("设置")

        layout.addStretch(1)
        layout.addWidget(self.btn_mic)
        layout.addStretch(1)
        layout.addWidget(self.btn_history)
        layout.addStretch(1)
        layout.addWidget(self.btn_settings)
        layout.addStretch(1)
