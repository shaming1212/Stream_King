from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class TopBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("topBar")
        self.setFixedHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 0)

        self.menu_btn = QPushButton("⚄")
        self.menu_btn.setObjectName("menuButton")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.logo = QLabel("AURA")
        self.logo.setObjectName("logoLabel")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.avatar = QPushButton("\U0001F464")
        self.avatar.setObjectName("avatarButton")
        self.avatar.setFixedSize(36, 36)
        self.avatar.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self.menu_btn)
        layout.addWidget(self.logo, 1)
        layout.addWidget(self.avatar)
