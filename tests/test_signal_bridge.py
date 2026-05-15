import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_bridge():
    from PyQt6.QtCore import QCoreApplication
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])

    from gui.signal_bridge import VoiceEngineBridge, CameraBridge
    vb = VoiceEngineBridge()
    assert vb.engine is not None

    cb = CameraBridge()
    assert cb.camera is not None
    cb.release()
