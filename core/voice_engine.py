import re
import logging
import time
import numpy as np
import keyboard
import sounddevice as sd
import threading

logger = logging.getLogger("voice_engine")

from core.config import SAMPLE_RATE, HOTKEY_VOICE, MODEL_NAME, VAD_MODEL, PUNC_MODEL, MODEL_PROFILE


class VoiceEngine:
    def __init__(self):
        self.model = None
        self.recording = False
        self.processing = False
        self._processing_lock = threading.Lock()
        self.audio_buffer = []
        self._audio_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self.stream = None
        self._max_frames = SAMPLE_RATE * 120
        self._hotkey_armed = False
        self._rel_handlers = []

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

            logger.info("loading ASR profile=%s model=%s", MODEL_PROFILE, MODEL_NAME)
            model_path = snapshot_download(MODEL_NAME)
            vad_path = snapshot_download(VAD_MODEL) if VAD_MODEL else None
            punc_path = snapshot_download(PUNC_MODEL) if PUNC_MODEL else None

            kwargs = {
                "model": model_path,
                "disable_update": True,
            }
            if vad_path:
                kwargs["vad_model"] = vad_path
            if punc_path:
                kwargs["punc_model"] = punc_path

            self.model = AutoModel(**kwargs)
            logger.info("model ready: profile=%s, punc=%s", MODEL_PROFILE, "on" if punc_path else "off")
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
        self._rel_handlers = []
        self._hotkey_armed = False

        keyboard.add_hotkey(HOTKEY_VOICE, self._on_press, suppress=True, trigger_on_release=False)
        self._rel_handlers.append(keyboard.on_release_key('alt', self._on_release))
        self._rel_handlers.append(keyboard.on_release_key('1', self._on_release))

        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self._audio_callback)
        self.stream.start()

        if keyboard.is_pressed('alt') or keyboard.is_pressed('1'):
            threading.Thread(target=self._wait_and_arm, daemon=True).start()
        else:
            self._hotkey_armed = True

    def _wait_and_arm(self):
        while keyboard.is_pressed('alt') or keyboard.is_pressed('1'):
            time.sleep(0.05)
        time.sleep(0.1)
        self._hotkey_armed = True

    def stop_listening(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self._rel_handlers = []
        with self._state_lock:
            self.recording = False
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
        with self._state_lock:
            if self.processing or self.recording:
                return
            with self._audio_lock:
                self.audio_buffer = []
            self.recording = True
        self._emit(self.on_recording_start)

    def _on_release(self, event=None):
        with self._state_lock:
            if not self.recording:
                return
            self.recording = False
        self._emit(self.on_recording_stop)
        with self._processing_lock:
            if self.processing:
                return
            self.processing = True
        threading.Thread(target=self._process, daemon=True).start()

    def process_mobile_audio(self, b64_wav: str):
        """Process base64 WAV from mobile, resample to 16kHz if needed, run ASR"""
        import io
        import wave
        import base64

        def _run():
            try:
                parts = b64_wav.split(",")
                raw = parts[1] if len(parts) > 1 else b64_wav
                wav_bytes = base64.b64decode(raw)

                with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                    sr = wf.getframerate()
                    nch = wf.getnchannels()
                    nframes = wf.getnframes()
                    pcm = wf.readframes(nframes)

                audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
                if nch > 1:
                    audio = audio.reshape(-1, nch).mean(axis=1)

                if sr != SAMPLE_RATE:
                    import math
                    import scipy.signal
                    g = math.gcd(SAMPLE_RATE, sr)
                    audio = scipy.signal.resample_poly(audio, SAMPLE_RATE // g, sr // g)

                self._emit(self.on_processing)
                if self.model is None:
                    self._emit(self.on_error, "语音模型未就绪，请等待模型加载完成")
                    return
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
                self._emit(self.on_error, f"手机语音处理失败: {e}")

        threading.Thread(target=_run, daemon=True).start()

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
