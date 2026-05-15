import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_init():
    from core.camera_engine import CameraEngine
    c = CameraEngine()
    assert c.device_index == 0
    assert c.cap is None


def test_release_no_cap():
    from core.camera_engine import CameraEngine
    c = CameraEngine()
    c.release()
