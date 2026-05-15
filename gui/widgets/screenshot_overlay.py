from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QImage
import numpy as np


class ScreenshotOverlay(QWidget):
    sig_captured = pyqtSignal(int, int, int, int)
    sig_cancelled = pyqtSignal()

    def __init__(self, screen_img: np.ndarray):
        super().__init__()
        self._screen_img = screen_img
        h, w = screen_img.shape[:2]
        bgr = np.ascontiguousarray(screen_img[:, :, :3])
        qimg = QImage(bgr.tobytes(), w, h, w * 3, QImage.Format.Format_BGR888)
        self._bg = QPixmap.fromImage(qimg)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._start = None
        self._rect = QRect()
        self.showFullScreen()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._bg)
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if not self._rect.isNull():
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(self._rect, Qt.GlobalColor.transparent)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(0, 200, 160), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(self._rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._rect = QRect(self._start, self._start)
            self.update()

    def mouseMoveEvent(self, event):
        if self._start:
            self._rect = QRect(self._start, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._start:
            self._rect = QRect(self._start, event.pos()).normalized()
            self.close()
            if self._rect.width() > 4 and self._rect.height() > 4:
                self.sig_captured.emit(self._rect.x(), self._rect.y(), self._rect.width(), self._rect.height())
            else:
                self.sig_cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.sig_cancelled.emit()
