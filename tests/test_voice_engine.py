import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_init():
    from core.voice_engine import VoiceEngine
    ve = VoiceEngine()
    assert ve.model is None
    assert ve.recording is False
    assert ve.audio_buffer == []


def test_callbacks():
    from core.voice_engine import VoiceEngine
    ve = VoiceEngine()
    r = []
    ve.on_model_loading = lambda: r.append("loading")
    ve.on_model_ready = lambda: r.append("ready")
    ve.on_result = lambda t: r.append(t)

    ve._emit(ve.on_model_loading)
    ve._emit(ve.on_model_ready)
    ve._emit(ve.on_result, "hello")
    assert r == ["loading", "ready", "hello"]


def test_emit_safe():
    from core.voice_engine import VoiceEngine
    ve = VoiceEngine()
    ve._emit(None, "arg")
    ve._emit("not_callable", "arg")
