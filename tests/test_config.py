import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_constants():
    from core import config
    assert config.SAMPLE_RATE == 16000
    assert config.HOTKEY_VOICE == "alt+1"
    assert config.HOTKEY_CAMERA == "alt+2"
    assert config.HOTKEY_SCREENSHOT == "alt+3"
    assert config.WS_HOST == "0.0.0.0"
    assert isinstance(config.WS_PORT, int)
    assert config.WS_PORT > 0
    assert config.FILE_HOST == "0.0.0.0"
    assert isinstance(config.FILE_PORT, int)
    assert config.FILE_PORT > 0


def test_model_cache_env():
    from core import config
    assert os.environ.get("MODELSCOPE_CACHE") is not None
