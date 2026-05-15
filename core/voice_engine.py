import re
import logging
import numpy as np
import keyboard
import sounddevice as sd
import threading

logger = logging.getLogger("voice_engine")

from core.config import SAMPLE_RATE, HOTKEY_VOICE, MODEL_NAME, VAD_MODEL, PUNC_MODEL


class VoiceEngine:
    def __init__(self):
        self.model = None
        self.recording = False
        self.processing = False
        self._processing_lock = threading.Lock()
        self.audio_buffer = []
        self._audio_lock = threading.Lock()
        self.stream = None
        self._max_frames = SAMPLE_RATE * 120  # 120 秒上限
        self._hotkey_armed = False

        self.on_model_loading = None
        self.on_model_ready = None
        self.on_model_error = None
        self.on_recording_start = None
        self.on_recording_stop = None
        self.on_processing = None
        self.on_result = None
        self.on_error = None

    def _emit(self, cb, *args):
        if cb and callable(cb):
            cb(*args)

    def init_model(self):
        self._emit(self.on_model_loading)
        try:
            from modelscope.hub.snapshot_download import snapshot_download
            from funasr import AutoModel
            model_path = snapshot_download(MODEL_NAME)
            vad_path = snapshot_download(VAD_MODEL)
            punc_path = snapshot_download(PUNC_MODEL)
            logger.info("loading model: %s", MODEL_NAME)
            self.model = AutoModel(model=model_path, vad_model=vad_path, punc_model=punc_path, disable_update=True)
            logger.info("model ready")
            self._emit(self.on_model_ready)
        except Exception as e:
            logger.error("model load failed: %s", e)
            self._emit(self.on_model_error, str(e))

    def _audio_callback(self, indata, frames, _time, _status):
        if not self.recording:
            return
        with self._audio_lock:
            total = sum(b.shape[0] for b in self.audio_buffer) if self.audio_buffer else 0
            if total < self._max_frames:
                self.audio_buffer.append(indata.copy())

    def start_listening(self):
        keyboard.unhook_all()
        self._hotkey_armed = False
        keyboard.add_hotkey(HOTKEY_VOICE, self._on_press, suppress=True, trigger_on_release=False)
        keyboard.add_hotkey(HOTKEY_VOICE, self._on_release, suppress=True, trigger_on_release=True)
        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self._audio_callback)
        self.stream.start()
        threading.Timer(0.5, self._arm_hotkey).start()

    def _arm_hotkey(self):
        self._hotkey_armed = True

    def stop_listening(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def _on_press(self):
        if not self._hotkey_armed:
            return
        if not self.recording:
            with self._audio_lock:
                self.audio_buffer = []
            self.recording = True
            self._emit(self.on_recording_start)

    def _on_release(self, *_):
        if not self.recording:
            return
        self.recording = False
        self._emit(self.on_recording_stop)
        with self._processing_lock:
            if self.processing:
                return
            self.processing = True
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        try:
            with self._audio_lock:
                if not self.audio_buffer or self.model is None:
                    return
                audio = np.concatenate(self.audio_buffer, axis=0)
            self._emit(self.on_processing)
            audio = np.squeeze(audio)
            res = self.model.generate(input=audio, batch_size_s=300)
            if res and len(res) > 0:
                text = res[0]["text"]
                try:
                    from funasr.utils.postprocess_utils import rich_transcription_postprocess
                    text = rich_transcription_postprocess(text)
                except Exception:
                    pass
                text = re.sub(r"<\s*\|.*?\|\s*>", "", text).strip()
                if text:
                    self._emit(self.on_result, text)
                    return
            self._emit(self.on_error, "没听清，请重试")
        except Exception as e:
            self._emit(self.on_error, str(e))
        finally:
            with self._processing_lock:
                self.processing = False
