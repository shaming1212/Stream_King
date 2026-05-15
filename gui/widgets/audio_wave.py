import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QLinearGradient, QRadialGradient


class AudioWaveWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(190)
        self.setMinimumWidth(280)
        self._offset = 0.0
        self._noise = [random.uniform(0.8, 1.2) for _ in range(16)]
        self._active = False
        self._amp = 0.4

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(200)

    def set_active(self, active: bool):
        self._active = active
        self._timer.setInterval(33 if active else 200)

    def _tick(self):
        self._offset += 0.055
        i = int(self._offset * 2) % len(self._noise)
        self._noise[i] = max(0.6, min(1.4, self._noise[i] + random.uniform(-0.015, 0.015)))
        target = 1.0 if self._active else 0.4
        self._amp += (target - self._amp) * 0.08
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mid = h / 2.0
        pad = 12
        iw, ih = w - pad * 2, h - pad * 2

        pill = QRectF(pad, pad, iw, ih)
        bg = QLinearGradient(pad, pad, pad, pad + ih)
        bg.setColorAt(0.0, QColor(14, 14, 20))
        bg.setColorAt(0.5, QColor(10, 10, 16))
        bg.setColorAt(1.0, QColor(14, 14, 20))
        p.setBrush(bg)
        p.setPen(QPen(QColor(30, 30, 42), 1))
        p.drawRoundedRect(pill, ih / 2.0, ih / 2.0)

        glow = QRadialGradient(w / 2, mid, iw * 0.35)
        glow.setColorAt(0.0, QColor(0, 200, 160, 16))
        glow.setColorAt(0.4, QColor(120, 60, 220, 8))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.PenStyle.NoPen)
        gw, gh = iw * 0.7, ih * 0.7
        p.drawEllipse(QRectF(w / 2 - gw / 2, mid - gh / 2, gw, gh))

        self._draw_wave(p, w, mid, pad + 30,
                        QColor(0, 210, 170), QColor(0, 210, 170, 35),
                        0.019, 50, self._offset, 2.2, 9.0)
        self._draw_wave(p, w, mid, pad + 30,
                        QColor(160, 90, 240), QColor(160, 90, 240, 28),
                        0.026, 38, -self._offset * 1.35, 1.8, 7.0)
        p.end()

    def _draw_wave(self, p, w, mid, margin, color, glow_c, freq, amp, phase, lw, gw):
        path = QPainterPath()
        first = True
        end_x = w - margin
        for px in range(int(margin), int(end_x)):
            t = (px - margin) / (end_x - margin)
            env = math.exp(-((t - 0.5) ** 2) / (2 * 0.14 ** 2))
            ni = int(t * (len(self._noise) - 1))
            yv = (math.sin(px * freq + phase) * 0.55 +
                  math.sin(px * freq * 2.1 + phase * 1.6) * 0.28 +
                  math.sin(px * freq * 0.6 - phase * 0.4) * 0.17)
            y = mid + yv * amp * env * self._noise[ni] * self._amp
            if first:
                path.moveTo(px, y)
                first = False
            else:
                path.lineTo(px, y)
        p.setPen(QPen(glow_c, gw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(path)
        p.setPen(QPen(color, lw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(path)
